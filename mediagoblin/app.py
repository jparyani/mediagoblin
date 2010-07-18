import sys
import urllib

from beaker.middleware import SessionMiddleware
import routes
import pymongo
from webob import Request, exc

from mediagoblin import routing, util


class Error(Exception): pass
class ImproperlyConfigured(Error): pass


def load_controller(string):
    module_name, func_name = string.split(':', 1)
    __import__(module_name)
    module = sys.modules[module_name]
    func = getattr(module, func_name)
    return func


class MediagoblinApp(object):
    """
    Really basic wsgi app using routes and WebOb.
    """
    def __init__(self, database, user_template_path=None):
        self.template_env = util.get_jinja_env(user_template_path)
        self.db = database
        self.routing = routing.get_mapper()

    def __call__(self, environ, start_response):
        request = Request(environ)
        path_info = request.path_info
        route_match = self.routing.match(path_info)

        # No matching page?
        if route_match is None:
            # Try to do see if we have a match with a trailing slash
            # added and if so, redirect
            if not path_info.endswith('/') \
                    and request.method == 'GET' \
                    and self.routing.match(path_info + '/'):
                new_path_info = path_info + '/'
                if request.GET:
                    new_path_info = '%s?%s' % (
                        new_path_info, urllib.urlencode(request.GET))
                redirect = exc.HTTPTemporaryRedirect(location=new_path_info)
                return request.get_response(redirect)(environ, start_response)

            # Okay, no matches.  404 time!
            return exc.HTTPNotFound()(environ, start_response)

        controller = load_controller(route_match['controller'])
        request.start_response = start_response

        request.matchdict = route_match
        request.app = self
        request.template_env = self.template_env
        request.urlgen = routes.URLGenerator(self.routing, environ)
        request.session = request.environ['beaker.session']

        return controller(request)(environ, start_response)


def paste_app_factory(global_config, **kw):
    connection = pymongo.Connection()
    db = connection[kw.get('db_name', 'mediagoblin')]

    mgoblin_app = MediagoblinApp(
        db, user_template_path=kw.get('local_templates'))

    return mgoblin_app
