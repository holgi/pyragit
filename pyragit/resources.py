import pygit2

from pathlib import Path
from pyramid.exceptions import ConfigurationError


class BaseResource:

    def __init__(self, name, parent, tree_entry, request):
        self.__name__ = name
        self.__parent__ = parent
        self.pygit2_tree_entry = tree_entry
        self.request = request
        self._pygit2_object = None
    
    @property
    def pygit2_object(self):
        if self._pygit2_object is None:
            oid = self.pygit2_tree_entry.oid
            self._pygit2_object = self.request.repository[oid]
        return self._pygit2_object


class Folder(BaseResource):
    
    def __getitem__(self, key):
        if key.startswith('.'):
            raise KeyError
        try:
            tree_entry = self.pygit2_object[key]
            if tree_entry.type == 'blob':
                return File(key, self, tree_entry, self.request)
            elif tree_entry.type == 'tree':
                return Folder(key, self, tree_entry, self.request)
        except KeyError:
            pass
        markdown_file = key + self.request.markdown_extension
        blobs = (e for e in self.pygit2_object if e.type=='blob')
        for entry in blobs:
            if entry.name.lower() == markdown_file.lower():
                return Markdown(key, self, entry, self.request)
        raise KeyError
    
    def __iter__(self):
        allowed = (e for e in self.pygit2_object if not e.name.startswith('.'))
        ordered = sorted(allowed, key=lambda e: e.name.lower())
        trees = (e for e in ordered if e.type=='tree')
        for entry in trees:
            yield Folder(entry.name, self, entry, self.request)
        md_ext = self.request.markdown_extension
        blobs = (e for e in ordered if e.type=='blobs')
        texts = (e for e in blobs if e.name.endswith(md_ext))
        for entry in texts:
            name = key[:-len(md_ext)]
            yield Markdown(name, self, entry, self.request)                
    
    @property
    def index(self):
        try:
            return self['index']
        except KeyError:
            return None


class Root(Folder):

    def __init__(self, request):
        super().__init__(None, None, None, request)        
        head = request.repository.head
        commit = head.peel()
        self._pygit2_object = commit.tree


class File(BaseResource):

    @property
    def data(self):
        return self.pygit2_object.data
        
    @property
    def size(self):
        return self.pygit2_object.size


class Markdown(BaseResource):
    
    @property
    def text(self):
        return self.pygit2_object.data.decode('utf-8')



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
    
    markdown_extension = settings.get('pyragit.markdown_extension', None)
    if markdown_extension is None:
        raise ConfigurationError('Markdown Extension not set')

    # make request.markdown_extension available for use in Pyramid
    config.add_request_method(
        lambda r: markdown_extension,
        'markdown_extension',
        reify=True
        )

    # set the root factory for traverssal
    config.set_root_factory(Root)
