# GNU MediaGoblin -- federated, autonomous media hosting
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

import urllib

import routes
import mongokit
from webob import Request, exc

from mediagoblin import routing, util, models, storage, staticdirect


class Error(Exception): pass
class ImproperlyConfigured(Error): pass


class MediaGoblinApp(object):
    """
    Really basic wsgi app using routes and WebOb.
    """
    def __init__(self, connection, database_path,
                 public_store, queue_store,
                 staticdirector,
                 user_template_path=None):
        # Get the template environment
        self.template_env = util.get_jinja_env(user_template_path)
        
        # Set up storage systems
        self.public_store = public_store
        self.queue_store = queue_store

        # Set up database
        self.connection = connection
        self.db = connection[database_path]
        models.register_models(connection)

        # set up routing
        self.routing = routing.get_mapper()

        # set up staticdirector tool
        self.staticdirector = staticdirector

    def __call__(self, environ, start_response):
        request = Request(environ)
        path_info = request.path_info

        ## Routing / controller loading stuff
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

        controller = util.import_component(route_match['controller'])
        request.start_response = start_response

        ## Attach utilities to the request object
        request.matchdict = route_match
        request.urlgen = routes.URLGenerator(self.routing, environ)
        # Do we really want to load this via middleware?  Maybe?
        request.session = request.environ['beaker.session']
        util.setup_user_in_request(request)
        # Attach self as request.app
        # Also attach a few utilities from request.app for convenience?
        request.app = self
        request.template_env = self.template_env
        request.db = self.db
        request.staticdirect = self.staticdirector

        return controller(request)(environ, start_response)


def paste_app_factory(global_config, **kw):
    # Get the database connection
    connection = mongokit.Connection(
        kw.get('db_host'), kw.get('db_port'))

    # Set up the storage systems.
    public_store = storage.storage_system_from_paste_config(
        kw, 'publicstore')
    queue_store = storage.storage_system_from_paste_config(
        kw, 'queuestore')

    # Set up the staticdirect system
    if kw.has_key('direct_remote_path'):
        staticdirector = staticdirect.RemoteStaticDirect(
            kw['direct_remote_path'].strip())
    elif kw.has_key('direct_remote_paths'):
        staticdirector = staticdirect.MultiRemoteStaticDirect(
            dict([line.strip().split(' ', 1)
                  for line in kw['direct_remote_paths'].strip().splitlines()]))
    else:
        raise ImproperlyConfigured(
            "One of direct_remote_path or direct_remote_paths must be provided")

    mgoblin_app = MediaGoblinApp(
        connection, kw.get('db_name', 'mediagoblin'),
        public_store=public_store, queue_store=queue_store,
        staticdirector=staticdirector,
        user_template_path=kw.get('local_templates'))

    return mgoblin_app
