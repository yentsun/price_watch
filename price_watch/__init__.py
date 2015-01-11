from pkg_resources import get_distribution
from pyramid.config import Configurator
from pyramid_zodbconn import get_connection
from price_watch.models import StorageManager

__version__ = get_distribution('price_watch').version


def root_factory(request):
    conn = get_connection(request)
    return StorageManager(connection=conn)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['version'] = __version__
    config = Configurator(root_factory=root_factory, settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.scan()
    return config.make_wsgi_app()