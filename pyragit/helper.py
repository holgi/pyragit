import mistune

from mistune_contrib import highlight


class HighlightRenderer(highlight.HighlightMixin, mistune.Renderer):
    pass


def includeme(config):
    '''
    Initialize the resources for a Pyramid app.

    Activate this setup using ``config.include('pyragit.helper')``.

    '''

    # make request.render_markdown() available for use in Pyramid
    custom_renderer = HighlightRenderer()
    render_markdown = mistune.Markdown(renderer=custom_renderer)
    #render_markdown = mistune.Markdown()
    config.add_request_method(
        lambda request, text: render_markdown(text), 
        'render_markdown'
        )
    
