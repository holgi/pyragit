""" The view functions, connecting a context to an output """

import io
import mimetypes

from pyramid.view import view_config, notfound_view_config
from pyramid.response import FileIter


@view_config(
    context="pyragit.resources.Folder", renderer="templates/folder.jinja2"
)
def folder(context, request):
    """ renders a Folder context """
    return {}


@view_config(
    context="pyragit.resources.Markup", renderer="templates/markup.jinja2"
)
def markup(context, request):
    """ renders a markup context """
    return {}


@view_config(context="pyragit.resources.File")
def blob(context, request):
    """ a unrendered, binary file """
    output = io.BytesIO(context.data)
    output.seek(0)
    response = request.response
    response.app_iter = FileIter(output)
    headers = response.headers
    mime_type, _ = mimetypes.guess_type(context.__name__)
    if mime_type is None:
        mime_type = "application/download"
    headers["Content-Type"] = mime_type
    headers["Accept-Ranges"] = "bite"
    return response


@notfound_view_config(renderer="templates/not_found.jinja2")
def notfound(context, request):
    """ File not found view """
    return {}
