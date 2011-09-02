# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

import os
import urllib

import routes
from webob import Request, exc

from mediagoblin import routing, util
from mediagoblin.mg_globals import setup_globals
from mediagoblin.init.celery import setup_celery_from_config
from mediagoblin.init import (get_jinja_loader, get_staticdirector,
    setup_global_and_app_config, setup_workbench, setup_database,
    setup_storage)


class MediaGoblinApp(object):
    """
    WSGI application of MediaGoblin

    ... this is the heart of the program!
    """
    def __init__(self, config_path, setup_celery=True):
        """
        Initialize the application based on a configuration file.

        Arguments:
         - config_path: path to the configuration file we're opening.
         - setup_celery: whether or not to setup celery during init.
           (Note: setting 'celery_setup_elsewhere' also disables
           setting up celery.)
        """
        ##############
        # Setup config
        ##############

        # Open and setup the config
        global_config, app_config = setup_global_and_app_config(config_path)

        ##########################################
        # Setup other connections / useful objects
        ##########################################

        # Set up the database
        self.connection, self.db = setup_database()

        # Get the template environment
        self.template_loader = get_jinja_loader(
            app_config.get('user_template_path'))
        
        # Set up storage systems
        self.public_store, self.queue_store = setup_storage()

        # set up routing
        self.routing = routing.get_mapper()

        # set up staticdirector tool
        self.staticdirector = get_staticdirector(app_config)

        # Setup celery, if appropriate
        if setup_celery and not app_config.get('celery_setup_elsewhere'):
            if os.environ.get('CELERY_ALWAYS_EAGER'):
                setup_celery_from_config(
                    app_config, global_config,
                    force_celery_always_eager=True)
            else:
                setup_celery_from_config(app_config, global_config)

        #######################################################
        # Insert appropriate things into mediagoblin.mg_globals
        #
        # certain properties need to be accessed globally eg from
        # validators, etc, which might not access to the request
        # object.
        #######################################################

        setup_globals(app = self)

        # Workbench *currently* only used by celery, so this only
        # matters in always eager mode :)
        setup_workbench()

    def __call__(self, environ, start_response):
        request = Request(environ)
        path_info = request.path_info

        ## Routing / controller loading stuff
        route_match = self.routing.match(path_info)

        ## Attach utilities to the request object
        request.matchdict = route_match
        request.urlgen = routes.URLGenerator(self.routing, environ)
        # Do we really want to load this via middleware?  Maybe?
        request.session = request.environ['beaker.session']
        # Attach self as request.app
        # Also attach a few utilities from request.app for convenience?
        request.app = self
        request.locale = util.get_locale_from_request(request)
            
        request.template_env = util.get_jinja_env(
            self.template_loader, request.locale)
        request.db = self.db
        request.staticdirect = self.staticdirector

        util.setup_user_in_request(request)

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
                redirect = exc.HTTPFound(location=new_path_info)
                return request.get_response(redirect)(environ, start_response)

            # Okay, no matches.  404 time!
            request.matchdict = {}  # in case our template expects it
            return util.render_404(request)(environ, start_response)

        controller = util.import_component(route_match['controller'])
        request.start_response = start_response

        return controller(request)(environ, start_response)


def paste_app_factory(global_config, **app_config):
    mgoblin_app = MediaGoblinApp(app_config['config'])

    return mgoblin_app
