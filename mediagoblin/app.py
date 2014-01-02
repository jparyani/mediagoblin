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
import logging

from mediagoblin.routing import get_url_map
from mediagoblin.tools.routing import endpoint_to_controller

from werkzeug.wrappers import Request
from werkzeug.exceptions import HTTPException
from werkzeug.routing import RequestRedirect

from mediagoblin import meddleware, __version__
from mediagoblin.db.util import check_db_up_to_date
from mediagoblin.tools import common, session, translate, template
from mediagoblin.tools.response import render_http_exception
from mediagoblin.tools.theme import register_themes
from mediagoblin.tools import request as mg_request
from mediagoblin.media_types.tools import media_type_warning
from mediagoblin.mg_globals import setup_globals
from mediagoblin.init.celery import setup_celery_from_config
from mediagoblin.init.plugins import setup_plugins
from mediagoblin.init import (get_jinja_loader, get_staticdirector,
    setup_global_and_app_config, setup_locales, setup_workbench, setup_database,
    setup_storage)
from mediagoblin.tools.pluginapi import PluginManager, hook_transform
from mediagoblin.tools.crypto import setup_crypto
from mediagoblin.auth.tools import check_auth_enabled, no_auth_logout


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

        media_type_warning()

        setup_crypto()

        ##########################################
        # Setup other connections / useful objects
        ##########################################

        # Setup Session Manager, not needed in celery
        self.session_manager = session.SessionManager()

        # load all available locales
        setup_locales()

        # Set up plugins -- need to do this early so that plugins can
        # affect startup.
        _log.info("Setting up plugins.")
        setup_plugins()

        # Set up the database
        self.db = setup_database(app_config['run_migrations'])

        # Quit app if need to run dbupdate
        check_db_up_to_date()

        # Register themes
        self.theme_registry, self.current_theme = register_themes(app_config)

        # Get the template environment
        self.template_loader = get_jinja_loader(
            app_config.get('local_templates'),
            self.current_theme,
            PluginManager().get_template_paths()
            )

        # Check if authentication plugin is enabled and respond accordingly.
        self.auth = check_auth_enabled()
        if not self.auth:
            app_config['allow_comments'] = False

        # Set up storage systems
        self.public_store, self.queue_store = setup_storage()

        # set up routing
        self.url_map = get_url_map()

        # set up staticdirector tool
        self.staticdirector = get_staticdirector(app_config)

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

        # Compatibility with django, use request.args preferrably
        request.GET = request.args

        ## Routing / controller loading stuff
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
        session_manager = self.session_manager
        request.session = session_manager.load_session_from_cookie(request)
        # Attach self as request.app
        # Also attach a few utilities from request.app for convenience?
        request.app = self

        request.db = self.db
        request.staticdirect = self.staticdirector

        request.locale = translate.get_locale_from_request(request)
        request.template_env = template.get_jinja_env(
            self.template_loader, request.locale)

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

        # Log user out if authentication_disabled
        no_auth_logout(request)

        mg_request.setup_user_in_request(request)

        request.controller_name = None
        try:
            found_rule, url_values = map_adapter.match(return_rule=True)
            request.matchdict = url_values
        except RequestRedirect as response:
            # Deal with 301 responses eg due to missing final slash
            return response(environ, start_response)
        except HTTPException as exc:
            # Stop and render exception
            return render_http_exception(
                request, exc,
                exc.get_description(environ))(environ, start_response)

        controller = endpoint_to_controller(found_rule)
        # Make a reference to the controller's symbolic name on the request...
        # used for lazy context modification
        request.controller_name = found_rule.endpoint

        # pass the request through our meddleware classes
        try:
            for m in self.meddleware:
                response = m.process_request(request, controller)
                if response is not None:
                    return response(environ, start_response)
        except HTTPException as e:
            return render_http_exception(
                request, e,
                e.get_description(environ))(environ, start_response)

        request.start_response = start_response

        # get the Http response from the controller
        try:
            response = controller(request)
        except HTTPException as e:
            response = render_http_exception(
                request, e, e.get_description(environ))

        # pass the response through the meddlewares
        try:
            for m in self.meddleware[::-1]:
                m.process_response(request, response)
        except HTTPException as e:
            response = render_http_exception(
                request, e, e.get_description(environ))

        session_manager.save_session_to_cookie(request.session,
                                               request, response)

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
    mgoblin_app = hook_transform('wrap_wsgi', mgoblin_app)

    return mgoblin_app
