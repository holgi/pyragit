""" Pyragit: Pyramid Traversal Resources """


import functools
from datetime import datetime

import pygit2
from pyramid.exceptions import ConfigurationError


class BaseResource:
    """ base class for all resources """

    def __init__(self, tree_entry, parent):
        self.__name__ = tree_entry.name
        self.__parent__ = parent
        self.pygit2_tree_entry = tree_entry
        self.request = parent.request

    @property
    @functools.lru_cache(maxsize=128)
    def pygit2_object(self):
        """ lazy loading of the pygit2 object """
        oid = self.pygit2_tree_entry.oid
        return self.request.repository[oid]

    @property
    def type(self):
        """ returns the type of the resource, either 'tree' or 'blob' """
        # Root has no tree entry, but is a Folder
        if self.__name__ is None:
            return "tree"
        elif self.pygit2_tree_entry.type == pygit2.GIT_OBJ_TREE:
            return "tree"
        else:
            return "blob"

    @property
    @functools.lru_cache(maxsize=128)
    def last_commit(self):
        """ get the last commit of the resource

        from https://stackoverflow.com/questions/13293052/pygit2-blob-history
        """
        # get the relative path inside the git repo and
        # remove trailing and leading slashes if present
        git_path = self.request.resource_path(self)
        git_path = git_path[1:]
        if git_path.endswith("/"):
            git_path = git_path[:-1]

        # the latest git object id to compare earlier commits to
        last_oid = self.pygit2_tree_entry.oid
        last_commit = None
        repo = self.request.repository
        # walk through every commit, starting at the latests
        for commit in repo.walk(repo.head.target, pygit2.GIT_SORT_TIME):
            # get the object id of the git path if it exists or None
            if git_path in commit.tree:
                oid = commit.tree[git_path].oid
            else:
                oid = None
            # has the object id changed to the commit before?
            # will be False on the latest commit since the current object id
            # was stored before
            if oid != last_oid:
                return last_commit

            # the current commit object is now the last commit object
            last_commit = commit

        # looped through all commits, never changed, therefore it was present
        # in the first commit ever made
        return last_commit

    @property
    def author(self):
        return self.last_commit.author.name

    @property
    def date(self):
        return datetime.fromtimestamp(float(self.last_commit.author.time))


class Folder(BaseResource):
    """ Resource representing a git tree (like a folder in a file system) """

    @property
    @functools.lru_cache(maxsize=128)
    def index(self):
        """ get the markup index file of the folder or None """
        blobs = (
            e for e in self.pygit2_object if e.type == pygit2.GIT_OBJ_BLOB
        )
        index_files = (e for e in blobs if e.name.lower().startswith("index."))
        for entry in index_files:
            renderer = self.request.get_markup_renderer(entry.name)
            if renderer:
                return Markup(entry, self, renderer)
        return None

    def __getitem__(self, key):
        """ Dict like access to child resources """

        # hidden files (starting with a dot) are forbidden to access
        if key.startswith("."):
            raise KeyError

        tree_entry = self.pygit2_object[key]
        if tree_entry.type == pygit2.GIT_OBJ_TREE:
            return Folder(tree_entry, self)

        if tree_entry.type != pygit2.GIT_OBJ_BLOB:
            # non file entry, might be a git note object
            # or something else
            raise KeyError

        renderer = self.request.get_markup_renderer(key)
        if renderer is None:
            return File(tree_entry, self)
        else:
            return Markup(tree_entry, self, renderer)

    def __iter__(self):
        """ iterate over renderable child resources """
        # exclude hidden files and order by lowre case name
        allowed = (e for e in self.pygit2_object if not e.name.startswith("."))
        ordered = sorted(allowed, key=lambda e: e.name.lower())
        # first list the folders
        trees = (e for e in ordered if e.type == pygit2.GIT_OBJ_TREE)
        for entry in trees:
            yield Folder(entry, self)
        # then list the markup files
        blobs = (e for e in ordered if e.type == pygit2.GIT_OBJ_BLOB)
        # except the index file used
        index_name = self.index.__name__ if self.index else None
        non_index = (e for e in blobs if e.name != index_name)
        for entry in non_index:
            renderer = self.request.get_markup_renderer(entry.name)
            if renderer:
                yield Markup(entry, self, renderer)


class Root(Folder):
    """ the root resource for traversal """

    def __init__(self, request):
        self.__name__ = None
        self.__parent__ = None
        self.request = request

    @property
    def pygit2_object(self):
        """ lazy loading of the pygit2 object not required on root resource"""
        return self.last_commit.tree

    @property
    def last_commit(self):
        """ get the last commit of the resource

        On the root resource, this is only a simple lookup
        """
        return self.request.repository.head.peel()


class File(BaseResource):
    """ Resource for a (binary) file """

    @property
    def data(self):
        """ the binary data of the file """
        return self.pygit2_object.data

    @property
    def size(self):
        """ the size of the binary data of the file """
        return self.pygit2_object.size


class Markup(BaseResource):
    """ Resource for a markup file that could be rendered """

    def __init__(self, tree_entry, parent, rendering_func):
        super().__init__(tree_entry, parent)
        self.renderer = rendering_func

    @property
    def text(self):
        """ access the text content of the file """
        return self.pygit2_object.data.decode("utf-8")

    def render(self):
        """ returned the rendered representation of the markup file"""
        return self.renderer(self.text)


def includeme(config):
    """
    Initialize the resources for a Pyramid app.

    Activate this setup using ``config.include('pyragit.resources')``.

    """
    settings = config.get_settings()

    repo_path = settings.get("pyragit.repository_path", None)
    if repo_path is None:
        raise ConfigurationError("Repository Path not set")

    # make request.repository available for use in Pyramid
    config.add_request_method(
        lambda r: pygit2.Repository(repo_path, pygit2.GIT_REPOSITORY_OPEN_BARE), "repository", reify=True
    )

    # set the root factory for traverssal
    config.set_root_factory(Root)
