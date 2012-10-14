# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
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
import logging

from mediagoblin.routing import url_map, view_functions, add_route

from werkzeug.wrappers import Request
from werkzeug.exceptions import HTTPException, NotFound

from mediagoblin import meddleware, __version__
from mediagoblin.tools import common, translate, template
from mediagoblin.tools.response import render_404
from mediagoblin.tools.theme import register_themes
from mediagoblin.tools import request as mg_request
from mediagoblin.mg_globals import setup_globals
from mediagoblin.init.celery import setup_celery_from_config
from mediagoblin.init.plugins import setup_plugins
from mediagoblin.init import (get_jinja_loader, get_staticdirector,
    setup_global_and_app_config, setup_workbench, setup_database,
    setup_storage, setup_beaker_cache)
from mediagoblin.tools.pluginapi import PluginManager


_log = logging.getLogger(__name__)


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
        _log.info("GNU MediaGoblin %s main server starting", __version__)
        _log.debug("Using config file %s", config_path)
        ##############
        # Setup config
        ##############

        # Open and setup the config
        global_config, app_config = setup_global_and_app_config(config_path)

        ##########################################
        # Setup other connections / useful objects
        ##########################################

        # Set up plugins -- need to do this early so that plugins can
        # affect startup.
        _log.info("Setting up plugins.")
        setup_plugins()

        # Set up the database
        self.connection, self.db = setup_database()

        # Register themes
        self.theme_registry, self.current_theme = register_themes(app_config)

        # Get the template environment
        self.template_loader = get_jinja_loader(
            app_config.get('local_templates'),
            self.current_theme,
            PluginManager().get_template_paths()
            )

        # Set up storage systems
        self.public_store, self.queue_store = setup_storage()

        # set up routing
        self.url_map = url_map

        for route in PluginManager().get_routes():
            add_route(*route)

        # set up staticdirector tool
        self.staticdirector = get_staticdirector(app_config)

        # set up caching
        self.cache = setup_beaker_cache()

        # Setup celery, if appropriate
        if setup_celery and not app_config.get('celery_setup_elsewhere'):
            if os.environ.get('CELERY_ALWAYS_EAGER', 'false').lower() == 'true':
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

    def call_backend(self, environ, start_response):
        request = Request(environ)

        ## Compatibility webob -> werkzeug
        request.GET = request.args
        request.accept_language = request.accept_languages
        request.accept = request.accept_mimetypes

        ## Routing / controller loading stuff
        path_info = request.path
        map_adapter = self.url_map.bind_to_environ(request.environ)

        # By using fcgi, mediagoblin can run under a base path
        # like /mediagoblin/. request.path_info contains the
        # path inside mediagoblin. If the something needs the
        # full path of the current page, that should include
        # the basepath.
        # Note: urlgen and routes are fine!
        request.full_path = environ["SCRIPT_NAME"] + request.path
        # python-routes uses SCRIPT_NAME. So let's use that too.
        # The other option would be:
        # request.full_path = environ["SCRIPT_URL"]

        # Fix up environ for urlgen
        # See bug: https://bitbucket.org/bbangert/routes/issue/55/cache_hostinfo-breaks-on-https-off
        if environ.get('HTTPS', '').lower() == 'off':
            environ.pop('HTTPS')

        ## Attach utilities to the request object
        # Do we really want to load this via middleware?  Maybe?
        request.session = request.environ['beaker.session']
        # Attach self as request.app
        # Also attach a few utilities from request.app for convenience?
        request.app = self

        request.db = self.db
        request.staticdirect = self.staticdirector

        mg_request.setup_user_in_request(request)

        try:
            endpoint, url_values = map_adapter.match()
            request.matchdict = url_values

            request.locale = translate.get_locale_from_request(request)
            request.template_env = template.get_jinja_env(
                self.template_loader, request.locale)
        except NotFound as exc:
            return NotImplemented
            return render_404(request)(environ, start_response)
        except HTTPException as exc:
            # Support legacy webob.exc responses
            return exc(environ, start_response)

        def build_proxy(endpoint, **kw):
            try:
                qualified = kw.pop('qualified')
            except KeyError:
                qualified = False

            return map_adapter.build(
                    endpoint,
                    values=dict(**kw),
                    force_external=qualified)

        request.urlgen = build_proxy

        view_func = view_functions[endpoint]

        # import the endpoint, or if it's already a callable, call that
        if isinstance(view_func, unicode) \
                or isinstance(view_func, str):
            controller = common.import_component(view_func)
        else:
            controller = view_func

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

    def __call__(self, environ, start_response):
        ## If more errors happen that look like unclean sessions:
        # self.db.check_session_clean()

        try:
            return self.call_backend(environ, start_response)
        finally:
            # Reset the sql session, so that the next request
            # gets a fresh session
            self.db.reset_after_request()


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
