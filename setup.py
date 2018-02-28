import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'mistune',
    'mistune-contrib',
    'plaster_pastedeploy',
    'pygit2',
    'pygments',
    'pyramid',
    'pyramid_debugtoolbar',
    'pyramid_jinja2',
    'waitress',
]

tests_require = [
    'flake8',
    'pytest',
    'pytest-cov',
    'WebTest >= 1.3.1',  # py3 compat
]

setup(
    name='pyragit',
    version='0.1',
    description='Simple rendering of markdown files in a git repository',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Development Status :: 3 - Alpha',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'License :: Other/Proprietary License'
    ],
    author='Holger Frey',
    author_email='mail@holgerfrey.de',
    url='https://github.com/holgi/pyragit',
    keywords='web pyramid pylons markdown git',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = pyragit:main',
        ],
    },
)
