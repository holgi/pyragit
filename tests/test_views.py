""" Tests for pyragit.views module """

import pytest
from pyramid.testing import DummyRequest, DummyResource


def test_folder():
    from pyragit.views import folder

    assert folder(None, None) == {}


def test_markup():
    from pyragit.views import markup

    assert markup(None, None) == {}


def test_notfound():
    from pyragit.views import notfound

    assert notfound(None, None) == {}


@pytest.mark.parametrize(
    "filename, content_type",
    [
        ("no extension", "application/download"),
        ("extension.unknown", "application/download"),
        ("known extension.jpg", "image/jpeg"),
    ],
)
def test_blob(filename, content_type):
    from pyragit.views import blob

    data = b"some binary data"
    context = DummyResource(__name__=filename, data=data)
    request = DummyRequest()
    result = blob(context, request)
    assert result.headers["Content-Type"] == content_type
    assert result.headers["Accept-Ranges"] == "bite"
    assert list(result.app_iter) == [b"some binary data"]
