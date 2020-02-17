Pyragit - simple rendering of markdown files in a git repo
==========================================================

This [Pyramid](https://trypyramid.com)-app renders text files in a git repository and allows access to (sub) folders.

A file with an '.md' extension is considered a [markdown](https://daringfireball.net/projects/markdown/) file and is rendered when accessed (also works on .txt files)


Getting Started
---------------

- Change directory into your newly created project.

    cd pyragit

- Setup the development environment.

    make devenv
    Source .venv/bin/activate

- Run your project.

    pserve development.ini
