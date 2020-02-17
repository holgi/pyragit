""" setup of the markup renderers """

import mistune
from mistune_contrib import highlight


class HighlightRenderer(highlight.HighlightMixin, mistune.Renderer):
    """ Markdown renderer with syntax highlighting"""

    pass


def render_text(content):
    """ a simple renderer for text documents: replace new lines with <br> """
    return "<br>".join(content.splitlines())


def includeme(config):
    """
    configures the rendering engines and attaches them to the request

    Activate this setup using ``config.include('pyragit.markdown')``.
    """
    md_renderer = HighlightRenderer(inlinestyles=False, linenos=False)
    render_markdown = mistune.Markdown(renderer=md_renderer)

    renderer_dict = {".md": render_markdown, ".txt": render_text}

    def get_markup_renderer(filename):
        name, dot, ext = filename.rpartition(".")
        complete_extension = dot + ext
        return renderer_dict.get(complete_extension, None)

    config.add_request_method(
        lambda request, filename: get_markup_renderer(filename),
        "get_markup_renderer",
    )
