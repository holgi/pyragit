''' Pyragit

Simple rendering of markdown files in a git repository

'''

from pyramid.config import Configurator


def main(global_config, **settings):
    ''' This function returns a Pyramid WSGI application. '''
    
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('pyragit.resources')
    config.include('pyragit.markup')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.scan()
        
    return config.make_wsgi_app()


