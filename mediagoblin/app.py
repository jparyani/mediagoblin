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

from mediagoblin import routing, meddleware
from mediagoblin.tools import common, translate, template
from mediagoblin.tools.response import render_404
from mediagoblin.tools import request as mg_request
from mediagoblin.mg_globals import setup_globals
from mediagoblin.init.celery import setup_celery_from_config
from mediagoblin.init import (get_jinja_loader, get_staticdirector,
    setup_global_and_app_config, setup_workbench, setup_database,
    setup_storage, setup_beaker_cache)


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
            app_config.get('local_templates'))

        # Set up storage systems
        self.public_store, self.queue_store = setup_storage()

        # set up routing
        self.routing = routing.get_mapper()

        # set up staticdirector tool
        self.staticdirector = get_staticdirector(app_config)

        # set up caching
        self.cache = setup_beaker_cache()

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

        setup_globals(app=self)

        # Workbench *currently* only used by celery, so this only
        # matters in always eager mode :)
        setup_workbench()

        # instantiate application meddleware
        self.meddleware = [common.import_component(m)(self)
                           for m in meddleware.ENABLED_MEDDLEWARE]

    def __call__(self, environ, start_response):
        request = Request(environ)

        ## Routing / controller loading stuff
        path_info = request.path_info
        route_match = self.routing.match(path_info)

        # By using fcgi, mediagoblin can run under a base path
        # like /mediagoblin/. request.path_info contains the
        # path inside mediagoblin. If the something needs the
        # full path of the current page, that should include
        # the basepath.
        # Note: urlgen and routes are fine!
        request.full_path = environ["SCRIPT_NAME"] + request.path_info
        # python-routes uses SCRIPT_NAME. So let's use that too.
        # The other option would be:
        # request.full_path = environ["SCRIPT_URL"]

        ## Attach utilities to the request object
        request.matchdict = route_match
        request.urlgen = routes.URLGenerator(self.routing, environ)
        # Do we really want to load this via middleware?  Maybe?
        request.session = request.environ['beaker.session']
        # Attach self as request.app
        # Also attach a few utilities from request.app for convenience?
        request.app = self
        request.locale = translate.get_locale_from_request(request)

        request.template_env = template.get_jinja_env(
            self.template_loader, request.locale)
        request.db = self.db
        request.staticdirect = self.staticdirector

        mg_request.setup_user_in_request(request)

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
            return render_404(request)(environ, start_response)

        controller = common.import_component(route_match['controller'])

        # pass the request through our meddleware classes
        for m in self.meddleware:
            response = m.process_request(request, controller)
            if response is not None:
                return response(environ, start_response)

        request.start_response = start_response

        # get the response from the controller
        response = controller(request)

        # pass the response through the meddleware
        for m in self.meddleware[::-1]:
            m.process_response(request, response)

        return response(environ, start_response)


def paste_app_factory(global_config, **app_config):
    configs = app_config['config'].split()
    mediagoblin_config = None
    for config in configs:
        if os.path.exists(config) and os.access(config, os.R_OK):
            mediagoblin_config = config
            break

    if not mediagoblin_config:
        raise IOError("Usable mediagoblin config not found.")

    mgoblin_app = MediaGoblinApp(mediagoblin_config)

    return mgoblin_app
