''' Tests for pyragit.resources module '''

import pygit2
import pytest

from pyramid.testing import DummyRequest, DummyResource

from . import repo_path


def dummy_get_markup_renderer(name):
    if name.endswith('.md'):
        return 'markdown'
    if name.endswith('.txt'):
        return 'text'
    return None

@pytest.fixture
def request_object(repo_path):
    repository = pygit2.Repository(repo_path)
    yield DummyRequest(
        repository=repository,
        get_markup_renderer=dummy_get_markup_renderer
        )

@pytest.fixture
def root(request_object):
    from pyragit.resources import Root
    yield Root(request_object)


# tests

@pytest.mark.parametrize(
    'name,gitid', [
        ('down', 'be09d04119a9db0b3a41a81d5afa3d50b811d352'),
        ('index.md', 'aaf471a51ed8df6929cd32a80c8e8cf97253d928'),
        ('desrcription.md', 'aaf471a51ed8df6929cd32a80c8e8cf97253d928'),
        ('multi-commit.md', 'ff1b13b250c1835817895f5f9399f40c6d675e75')
        ]
    )
def test_base_resource_last_commmit(root, name, gitid):
    resource = root[name]
    last_commit = resource.last_commit
    assert isinstance(last_commit, pygit2.Commit)
    assert last_commit.hex == gitid
  

def test_root_last_commit(root):
    assert isinstance(root.last_commit, pygit2.Commit)
    assert root.last_commit.hex == '1aa435e34fa48546b03fa17cfca785e7b53fe0e4'
 

@pytest.mark.parametrize(
    'name,pygitobject', [('down', pygit2.Tree), 
    ('index.md', pygit2.Blob), ('kitten.jpg', pygit2.Blob)]
    )
def test_base_resource_pygit2_object(root, name, pygitobject):
    resource = root[name]
    assert isinstance(resource.pygit2_object, pygitobject)


@pytest.mark.parametrize(
    'name,resource_type', 
    [('down', 'tree'), ('index.md', 'blob'), ('kitten.jpg', 'blob')]
    )
def test_base_resource_type(root, name, resource_type):
    resource = root[name]
    assert resource.type == resource_type

    
def test_base_resource_author(root):
    assert root.author == 'Holger Frey'


def test_base_resource_date(root):
    import datetime
    assert root.date == datetime.datetime(2018, 3, 6, 16, 51, 36)


def test_root_init(request_object):
    from pyragit.resources import Root
    root = Root(request_object)
    assert root.__name__ is None
    assert root.__parent__ is None
    assert root.request == request_object


def test_root_pygit2_object(root):
    assert isinstance(root.pygit2_object, pygit2.Tree)
    assert root.pygit2_object.hex == 'a41a8c8e1212a3a8955fe25c42c3e0a62744be70'


def test_root_type(root):
    assert root.type == 'tree'


def test_folder_index_found(root):
    from pyragit.resources import Markup
    assert isinstance(root.index, Markup)
    
    
def test_folder_index_not_found(root):
    from pyragit.resources import Markup
    folder = root['down']['under']
    assert folder.index is None
    
    
def test_folder_getitem_folder(root):
    from pyragit.resources import Folder
    folder = root['down']
    assert isinstance(folder, Folder)
    assert folder.__name__ == 'down'
    assert folder.__parent__ == root
    assert isinstance(folder.pygit2_tree_entry, pygit2.TreeEntry)
    assert folder.request == root.request


def test_folder_getitem_markdown(root):
    from pyragit.resources import Markup
    markup = root['index.md']
    assert isinstance(markup, Markup)
    assert markup.__name__ == 'index.md'
    assert markup.__parent__ == root
    assert isinstance(markup.pygit2_tree_entry, pygit2.TreeEntry)
    assert markup.request == root.request
    assert markup.renderer == 'markdown'


def test_folder_getitem_text(root):
    from pyragit.resources import Markup
    folder = root['down']
    markup = folder['text-rendering.txt']
    assert isinstance(markup, Markup)
    assert markup.__name__ == 'text-rendering.txt'
    assert markup.__parent__ == folder
    assert isinstance(markup.pygit2_tree_entry, pygit2.TreeEntry)
    assert markup.request == root.request
    assert markup.renderer == 'text'


def test_folder_getitem_key_error_on_dot_file(root):
    with pytest.raises(KeyError):
        root['.not_accessible']


def test_folder_getitem_key_error_on_unknown_file(root):
    with pytest.raises(KeyError):
        root['unknown file']


def test_folder_iter_root(root):
    from pyragit.resources import Folder, Markup
    result = list(root)
    assert len(result) == 3
    entry_1, entry_2, entry_3 = result
    assert isinstance(entry_1, Folder)
    assert isinstance(entry_2, Markup)
    assert isinstance(entry_3, Markup)
    assert entry_1.__name__ == 'down'
    assert entry_2.__name__ == 'desrcription.md'  # typo in test repo
    assert entry_3.__name__ == 'multi-commit.md'


def test_folder_iter_folder(root):
    from pyragit.resources import Folder, Markup
    folder = root['down']
    result = list(folder)
    assert len(result) == 3
    entry_1, entry_2, entry_3 = result
    assert isinstance(entry_1, Folder)
    assert isinstance(entry_2, Markup)
    assert isinstance(entry_3, Markup)
    assert entry_1.__name__ == 'under'
    assert entry_2.__name__ == 'text-rendering.txt'
    assert entry_3.__name__ == 'traversing.md'


def test_file_data(root):
    fi = root['stream']
    assert fi.data == b'other or unknown files should be delivered as binary.'


def test_file_size(root):
    fi = root['stream']
    expected = len(b'other or unknown files should be delivered as binary.')
    assert fi.size == expected
    
    
def test_markup_text(root):
    markup = root['index.md']
    assert isinstance(markup.text, str)
    assert markup.text.startswith('Pyragit Test Repository\n')


def test_markup_render(root):
    markup = root['index.md']
    markup.renderer = lambda x: '>>' + x + '<<'
    rendered = markup.render()
    assert rendered.startswith('>>Pyragit Test Repository\n')
    assert rendered.endswith('project.<<')
