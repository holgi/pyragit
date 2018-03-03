''' Pyragit: Pyramid Traversal Resources '''


import pygit2
import functools

from datetime import datetime
from pathlib import Path
from pyramid.exceptions import ConfigurationError


class BaseResource:
    ''' base class for all resources '''

    def __init__(self, tree_entry, parent):
        self.__name__ = tree_entry.name
        self.__parent__ = parent
        self.pygit2_tree_entry = tree_entry
        self.request = parent.request
    
    @property
    @functools.lru_cache(maxsize=128)
    def pygit2_object(self):
        ''' lazy loading of the pygit2 object '''
        oid = self.pygit2_tree_entry.oid
        return self.request.repository[oid]

    @property
    def type(self):
        ''' returns the type of the resource, either 'tree' or 'blob' '''
        # Root has no tree entry, but is a Folder
        return 'tree' if self.__name__ is None else self.pygit2_tree_entry.type
    
    @property
    @functools.lru_cache(maxsize=128)
    def last_commit(self):
        ''' get the last commit of the resource 
        
        from https://stackoverflow.com/questions/13293052/pygit2-blob-history
        ''' 
        # loops through all the commits
        last_oid = None
        last_commit = None
        repo = self.request.repository
        for commit in repo.walk(repo.head.target, pygit2.GIT_SORT_TIME):

            # checks if the file exists
            if self.pygit2_tree_entry.name in commit.tree:
                # has it changed since last commit?
                # let's compare it's sha with the previous found sha
                oid = self.pygit2_tree_entry.oid
                has_changed = (oid != last_oid and last_oid)
                if has_changed:
                    return last_commit
                last_oid = oid
            else:
                last_oid = None

            last_commit = commit
            
        return last_commit

    @property
    def author(self):
        return self.last_commit.author.name
    
    @property
    def date(self):
        return datetime.fromtimestamp(float(self.last_commit.author.time))


class Folder(BaseResource):
    ''' Resource representing a git tree (like a folder in a file system) '''
    
    @property
    @functools.lru_cache(maxsize=128)
    def index(self):
        ''' get the markup index file of the folder or None '''
        blobs = (e for e in self.pygit2_object if e.type=='blob')
        index_files = (e for e in blobs if e.name.lower().startswith('index.'))
        for entry in index_files:
            renderer = self.request.get_markup_renderer(entry.name)
            if renderer:
                return Markup(entry, self, renderer)
        return None
    
    def __getitem__(self, key):
        ''' Dict like access to child resources '''
        
        # hidden files (starting with a dot) are forbidden to access
        if key.startswith('.'):
            raise KeyError
        
        tree_entry = self.pygit2_object[key]
        if tree_entry.type == 'tree':
            return Folder(tree_entry, self)
            
        if tree_entry.type != 'blob':
            # non file entry, might be a git note object
            # or something else
            raise KeyError
        
        renderer = self.request.get_markup_renderer(key)
        if renderer is None:
            return File(tree_entry, self)    
        else:
            return Markup(tree_entry, self, renderer)
    
    def __iter__(self):
        ''' iterate over renderable child resources '''
        # exclude hidden files and order by lowre case name
        allowed = (e for e in self.pygit2_object if not e.name.startswith('.'))
        ordered = sorted(allowed, key=lambda e: e.name.lower())
        # first list the folders
        trees = (e for e in ordered if e.type=='tree')
        for entry in trees:
            yield Folder(entry, self)
        # then list the markup files
        blobs = (e for e in ordered if e.type=='blob')
        # except the index file used
        index_name = self.index.__name__ if self.index else None
        non_index = (e for e in blobs if e.name != index_name)
        for entry in non_index:
            renderer = self.request.get_markup_renderer(entry.name)
            if renderer:
                yield Markup(entry, self, renderer)


class Root(Folder):
    ''' the root resource for traversal '''

    def __init__(self, request):
        self.__name__ = None
        self.__parent__ = None
        self.request = request   
    
    @property
    def pygit2_object(self):
        ''' lazy loading of the pygit2 object not required on root resource'''
        return self.last_commit.tree
        
    @property
    def last_commit(self):
        ''' get the last commit of the resource 
        
        On the root resource, this is only a simple lookup
        ''' 
        return self.request.repository.head.peel()


class File(BaseResource):
    ''' Resource for a (binary) file '''

    @property
    def data(self):
        ''' the binary data of the file '''
        return self.pygit2_object.data
        
    @property
    def size(self):
        ''' the size of the binary data of the file '''
        return self.pygit2_object.size


class Markup(BaseResource):
    ''' Resource for a markup file that could be rendered '''
    
    def __init__(self, tree_entry, parent, rendering_func):
        super().__init__(tree_entry, parent)
        self.renderer = rendering_func
    
    @property
    def text(self):
        ''' access the text content of the file '''
        return self.pygit2_object.data.decode('utf-8')
        
    def render(self):
        ''' returned the rendered representation of the markup file'''
        return self.renderer(self.text)



def includeme(config):
    '''
    Initialize the resources for a Pyramid app.

    Activate this setup using ``config.include('pyragit.resources')``.

    '''
    settings = config.get_settings()
    
    repo_path = settings.get('pyragit.repository_path', None)
    if repo_path is None:
        raise ConfigurationError('Repository Path not set')
    
    # make request.repository available for use in Pyramid
    config.add_request_method(
        lambda r: pygit2.Repository(repo_path),
        'repository',
        reify=True
        )
    
    # set the root factory for traverssal
    config.set_root_factory(Root)
