import os
from pyramid.config import Configurator
from pyramid_zodbconn import get_connection
from price_watch.models import StorageManager


def get_version():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, '../VERSION.txt')) as f:
        return f.read()


def root_factory(request):
    conn = get_connection(request)
    return StorageManager(connection=conn)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['version'] = get_version()
    config = Configurator(root_factory=root_factory, settings=settings)
    config.include('pyramid_mako')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.scan()
    return config.make_wsgi_app()