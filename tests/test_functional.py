""" functional tests for pyragit """

import pytest
import webtest

from . import repo_path  # Noqa: F401


@pytest.fixture(scope="module")
def testapp(repo_path):  # Noqa: F811
    """ fixture for using webtest """
    from pyragit import main

    settings = {"pyragit.repository_path": repo_path}
    app = main({}, **settings)
    testapp = webtest.TestApp(app)

    yield testapp


def check_explore_links(response, expected):
    explore = response.html.find(class_="pyragit-explore")
    found_links = explore.find_all("a")
    for link, href_and_text in zip(found_links, expected):
        href, text = href_and_text
        assert link["href"] == href
        assert " ".join(link.stripped_strings) == text


def test_startup_raises_error_on_not_set_repo_path():
    from pyragit import main
    from pyramid.exceptions import ConfigurationError

    test_settings = {}
    with pytest.raises(ConfigurationError):
        main({}, **test_settings)


def test_root(testapp):
    response = testapp.get("/")
    # renders index file
    assert "<base href=" not in response
    assert "<h1>Pyragit Test Repository</h1>" in response
    # test explore list
    explore_links = [
        ("/", "> ."),
        ("/down/", "d down/"),
        ("/desrcription.md/", "f desrcription.md"),
        ("/multi-commit.md/", "f multi-commit.md"),
    ]
    check_explore_links(response, explore_links)


def test_folder_with_index(testapp):
    response = testapp.get("/down/")
    # renders index file
    assert "<base href=" not in response
    assert '<h1>"Folders" are a thing</h1>' in response
    # test explore list
    explore_links = [
        ("/down/", "> ."),
        ("/", "d .."),
        ("/down/under/", "d under/"),
        ("/down/text-rendering.txt/", "f text-rendering.txt"),
        ("/down/traversing.md/", "f traversing.md"),
    ]
    check_explore_links(response, explore_links)


def test_folder_without_index(testapp):
    response = testapp.get("/down/under/")
    # renders index file
    assert "<base href=" not in response
    assert "<h1>Crivens" in response
    assert "If a markdown document is added at this path:" in response
    assert "~/down/under/index.md" in response
    # test explore list
    explore_links = [
        ("/down/under/", "> ."),
        ("/down/", "d .."),
        ("/down/under/missing-index.md/", "f missing-index.md"),
    ]
    check_explore_links(response, explore_links)


def test_markdown(testapp):
    response = testapp.get("/down/traversing.md")
    # renders index file
    assert '<base href="http://localhost/down/">' in response
    assert "<h1>Pyragit Traversing</h1>" in response
    # test explore list
    explore_links = [
        ("/down/", "d ."),
        ("/", "d .."),
        ("/down/under/", "d under/"),
        ("/down/text-rendering.txt/", "f text-rendering.txt"),
        ("/down/traversing.md/", "> traversing.md"),
    ]
    check_explore_links(response, explore_links)


def test_textfile(testapp):
    response = testapp.get("/down/text-rendering.txt")
    # renders index file
    assert '<base href="http://localhost/down/">' in response
    assert "<h1>" not in response
    assert "Text<br>should be<br>also<br>rendered" in response
    # test explore list
    explore_links = [
        ("/down/", "d ."),
        ("/", "d .."),
        ("/down/under/", "d under/"),
        ("/down/text-rendering.txt/", "> text-rendering.txt"),
        ("/down/traversing.md/", "f traversing.md"),
    ]
    check_explore_links(response, explore_links)


def test_download(testapp):
    response = testapp.get("/stream/")
    # renders index file
    assert response.headers["Content-Type"] == "application/download"
    expected_body = b"other or unknown files should be delivered as binary."
    assert response.body == expected_body


def test_file_not_found(testapp):
    response = testapp.get("/unknown/")
    # renders index file
    assert """The thing you've been looking for is not here.""" in response
    explore_links = [
        ("/", "d ."),
        ("/down/", "d down/"),
        ("/desrcription.md/", "f desrcription.md"),
        ("/multi-commit.md/", "f multi-commit.md"),
    ]
    check_explore_links(response, explore_links)
