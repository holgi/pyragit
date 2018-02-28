''' setup of the markdown renderer '''

import mistune

from mistune_contrib import highlight


class HighlightRenderer(highlight.HighlightMixin, mistune.Renderer):
    ''' Markdown renderer with syntax highlighting'''
    pass


def includeme(config):
    '''
    configures the markdown rendering engine and attaches it to the request

    Activate this setup using ``config.include('pyragit.markdown')``.

    '''

    # make request.render_markdown() available for use in Pyramid
    renderer = HighlightRenderer(inlinestyles=False, linenos=False)
    render_markdown = mistune.Markdown(renderer=renderer)
    config.add_request_method(
        lambda request, text: render_markdown(text), 
        'render_markdown'
        )
    
