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

import os
import urllib

import routes
from webob import Request, exc

from mediagoblin import routing, util, storage, staticdirect
from mediagoblin.config import (
    read_mediagoblin_config, generate_validation_report)
from mediagoblin.db.open import setup_connection_and_db_from_config
from mediagoblin.mg_globals import setup_globals
from mediagoblin.celery_setup import setup_celery_from_config
from mediagoblin.workbench import WorkbenchManager


class Error(Exception): pass
class ImproperlyConfigured(Error): pass


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
        global_config, validation_result = read_mediagoblin_config(config_path)
        app_config = global_config['mediagoblin']
        # report errors if necessary
        validation_report = generate_validation_report(
            global_config, validation_result)
        if validation_report:
            raise ImproperlyConfigured(validation_report)

        ##########################################
        # Setup other connections / useful objects
        ##########################################

        # Set up the database
        self.connection, self.db = setup_connection_and_db_from_config(
            app_config)

        # Get the template environment
        self.template_loader = util.get_jinja_loader(
            app_config.get('user_template_path'))
        
        # Set up storage systems
        self.public_store = storage.storage_system_from_paste_config(
            app_config, 'publicstore')
        self.queue_store = storage.storage_system_from_paste_config(
            app_config, 'queuestore')

        # set up routing
        self.routing = routing.get_mapper()

        # set up staticdirector tool
        if app_config.has_key('direct_remote_path'):
            self.staticdirector = staticdirect.RemoteStaticDirect(
                app_config['direct_remote_path'].strip())
        elif app_config.has_key('direct_remote_paths'):
            direct_remote_path_lines = app_config[
                'direct_remote_paths'].strip().splitlines()
            self.staticdirector = staticdirect.MultiRemoteStaticDirect(
                dict([line.strip().split(' ', 1)
                      for line in direct_remote_path_lines]))
        else:
            raise ImproperlyConfigured(
                "One of direct_remote_path or "
                "direct_remote_paths must be provided")

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

        setup_globals(
            app_config=app_config,
            global_config=global_config,

            # TODO: No need to set these two up as globals, we could
            # just read them out of mg_globals.app_config
            email_sender_address=app_config['email_sender_address'],
            email_debug_mode=app_config['email_debug_mode'],

            # Actual, useful to everyone objects
            db_connection=self.connection,
            database=self.db,
            public_store=self.public_store,
            queue_store=self.queue_store,
            workbench_manager=WorkbenchManager(app_config['workbench_path']))

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
                redirect = exc.HTTPFound(location=new_path_info)
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
        # Attach self as request.app
        # Also attach a few utilities from request.app for convenience?
        request.app = self
        request.locale = util.get_locale_from_request(request)
            
        request.template_env = util.get_jinja_env(
            self.template_loader, request.locale)
        request.db = self.db
        request.staticdirect = self.staticdirector

        util.setup_user_in_request(request)

        return controller(request)(environ, start_response)


def paste_app_factory(global_config, **app_config):
    mgoblin_app = MediaGoblinApp(app_config['config'])

    return mgoblin_app
