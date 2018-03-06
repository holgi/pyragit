''' Test package for pyragit. '''

import os
import pytest
import tempfile
import zipfile

from pyramid import testing


APP_SETTINGS = {}


# fixtures

@pytest.fixture(scope='session')
def app_config():
    ''' fixture for tests requiring a pyramid.testing setup '''
    with testing.testConfig(settings=APP_SETTINGS) as config:
        yield config


@pytest.fixture(scope='session')
def repo_path():
    ''' get the path to a temporary git repository '''
    tmpdir = tempfile.TemporaryDirectory()
    with zipfile.ZipFile('tests/test-repo.zip') as gitzip:
        gitzip.extractall(tmpdir.name)
    yield os.path.join(tmpdir.name, 'pyragit-test-repo.git')
