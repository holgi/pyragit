Pyragit - simple rendering of markdown files in a git repo
==========================================================

This [Pyramid](https://trypyramid.com)-app renders text files in a git repository and allows access to (sub) folders.

A file with an '.md' extension is considered a [markdown](https://daringfireball.net/projects/markdown/) file and is rendered when accessed.


Getting Started
---------------

- Change directory into your newly created project.

    cd pyragit

- Create a Python virtual environment.

    python3 -m venv env

- Upgrade packaging tools.

    env/bin/pip install --upgrade pip setuptools

- Install the project in editable mode

    env/bin/pip install -e .

- Run your project.

    env/bin/pserve development.ini
