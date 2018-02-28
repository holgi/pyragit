import io
import mimetypes

from pyramid.response import FileIter
from pyramid.view import view_config


@view_config(
    context='pyragit.resources.Folder', 
    renderer='templates/folder.jinja2'
    )
def folder(context, request):
    return { }


@view_config(
    context='pyragit.resources.Markdown', 
    renderer='templates/markdown.jinja2'
    )
def markdown(context, request):
    return { }


@view_config(context='pyragit.resources.File')
def blob(context, request):
    output = io.BytesIO(context.data)
    output.seek(0)
    response = request.response
    response.app_iter = FileIter(output)
    headers = response.headers
    mime_type, _ = mimetypes.guess_type(context.__name__)
    if mime_type is None:
        if context.__name__.endswith(request.markdown_extension):
            mime_type = 'text/plain'
        else:
            mime_type = 'application/download'
    headers['Content-Type'] = mime_type
    headers['Accept-Ranges'] = 'bite'
    return response
