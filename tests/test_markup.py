""" Tests for pyragit.markup module """


def test_render_text_one_line():
    from pyragit.markup import render_text

    text = "some text without line break"
    assert render_text(text) == text


def test_render_text_two_lines():
    from pyragit.markup import render_text

    text = """some text with
    one line break"""
    assert render_text(text) == "some text with<br>    one line break"


def test_render_text_three_lines():
    from pyragit.markup import render_text

    text = """some text
    with two
    line breaks"""
    assert render_text(text) == "some text<br>    with two<br>    line breaks"
