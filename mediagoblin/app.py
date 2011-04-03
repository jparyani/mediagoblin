# GNU Mediagoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import urllib

from beaker.middleware import SessionMiddleware
import routes
import mongokit
from webob import Request, exc

from mediagoblin import routing, util, models


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
    def __init__(self, connection, database_path, user_template_path=None):
        self.template_env = util.get_jinja_env(user_template_path)
        self.connection = connection
        self.db = connection[database_path]
        self.routing = routing.get_mapper()

        models.register_models(connection)

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
        request.db = self.db
        # Do we really want to load this via middleware?  Maybe?
        request.session = request.environ['beaker.session']
        util.setup_user_in_request(request)

        return controller(request)(environ, start_response)


def paste_app_factory(global_config, **kw):
    connection = mongokit.Connection(
        kw.get('db_host'), kw.get('db_port'))

    mgoblin_app = MediagoblinApp(
        connection, kw.get('db_name', 'mediagoblin'),
        user_template_path=kw.get('local_templates'))

    return mgoblin_app
