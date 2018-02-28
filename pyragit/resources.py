''' Pyragit: Pyramid Traversal Resources '''


import pygit2

from pathlib import Path
from pyramid.exceptions import ConfigurationError


class BaseResource:
    ''' base class for all resources '''

    def __init__(self, name, parent, tree_entry, request):
        self.__name__ = name
        self.__parent__ = parent
        self.pygit2_tree_entry = tree_entry
        self.request = request
        self._pygit2_object = None
    
    @property
    def pygit2_object(self):
        ''' lazy loading of the pygit2 object '''
        if self._pygit2_object is None:
            oid = self.pygit2_tree_entry.oid
            self._pygit2_object = self.request.repository[oid]
        return self._pygit2_object


class Folder(BaseResource):
    ''' Resource representing a git tree (like a folder in a file system) '''
    
    def __getitem__(self, key):
        ''' Dict like access to child resources '''
        
        # hidden files (starting with a dot) are forbidden to access
        if key.startswith('.'):
            raise KeyError
        
        # try to directly access a tree entry, 
        # only blob (binary file) and trees (folders) are allowed
        try:
            tree_entry = self.pygit2_object[key]
            if tree_entry.type == 'blob':
                return File(key, self, tree_entry, self.request)
            elif tree_entry.type == 'tree':
                return Folder(key, self, tree_entry, self.request)
        except KeyError:
            pass
        
        # look for a text-file, that should be rendered
        markdown = self._search_markdown_file(key)
        if markdown:
            return markdown         
       
        # nothing found, raise Error
        raise KeyError
    
    def _search_markdown_file(self, name):
        ''' look for a  markdown file '''
        markdown_file = name + self.request.markdown_extension
        blobs = (e for e in self.pygit2_object if e.type=='blob')
        for entry in blobs:
            if entry.name.lower() == markdown_file.lower():
                return Markdown(name, self, entry, self.request)
        return None
    
    
    def __iter__(self):
        ''' iterate over renderable child resources '''
        # exclude hidden files and order by lowre case name
        allowed = (e for e in self.pygit2_object if not e.name.startswith('.'))
        ordered = sorted(allowed, key=lambda e: e.name.lower())
        # first list the folders
        trees = (e for e in ordered if e.type=='tree')
        for entry in trees:
            yield Folder(entry.name, self, entry, self.request)
        # then list the markdown files
        md_ext = self.request.markdown_extension
        blobs = (e for e in ordered if e.type=='blob')
        texts = (e for e in blobs if e.name.endswith(md_ext))
        for entry in texts:
            name = entry.name[:-len(md_ext)]
            yield Markdown(name, self, entry, self.request)                
    
    @property
    def index(self):
        ''' get the markdown index file of the folder or None '''
        return self._search_markdown_file('index')


class Root(Folder):
    ''' the root resource for traversal '''

    def __init__(self, request):
        super().__init__(None, None, None, request)        
        head = request.repository.head
        commit = head.peel()
        self._pygit2_object = commit.tree


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


class Markdown(BaseResource):
    ''' Resource for a Markdown file that could be rendered '''
    
    @property
    def text(self):
        ''' access the text content of the file '''
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
