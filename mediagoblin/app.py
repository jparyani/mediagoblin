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
from contextlib import contextmanager

from mediagoblin.routing import get_url_map
from mediagoblin.tools.routing import endpoint_to_controller

from werkzeug.wrappers import Request
from werkzeug.exceptions import HTTPException
from werkzeug.routing import RequestRedirect
from werkzeug.wsgi import SharedDataMiddleware

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

from mediagoblin.tools.transition import DISABLE_GLOBALS


_log = logging.getLogger(__name__)


class Context(object):
    """
    MediaGoblin context object.

    If a web request is being used, a Flask Request object is used
    instead, otherwise (celery tasks, etc), attach things to this
    object.

    Usually appears as "ctx" in utilities as first argument.
    """
    pass


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
        self.global_config, self.app_config = setup_global_and_app_config(config_path)

        media_type_warning()

        setup_crypto(self.app_config)

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
        if DISABLE_GLOBALS:
            self.db_manager = setup_database(self)
        else:
            self.db = setup_database(self)

        # Quit app if need to run dbupdate
        ## NOTE: This is currently commented out due to session errors..
        ##  We'd like to re-enable!
        # check_db_up_to_date()

        # Register themes
        self.theme_registry, self.current_theme = register_themes(self.app_config)

        # Get the template environment
        self.template_loader = get_jinja_loader(
            self.app_config.get('local_templates'),
            self.current_theme,
            PluginManager().get_template_paths()
            )

        # Check if authentication plugin is enabled and respond accordingly.
        self.auth = check_auth_enabled()
        if not self.auth:
            self.app_config['allow_comments'] = False

        # Set up storage systems
        self.public_store, self.queue_store = setup_storage()

        # set up routing
        self.url_map = get_url_map()

        # set up staticdirector tool
        self.staticdirector = get_staticdirector(self.app_config)

        # Setup celery, if appropriate
        if setup_celery and not self.app_config.get('celery_setup_elsewhere'):
            if os.environ.get('CELERY_ALWAYS_EAGER', 'false').lower() == 'true':
                setup_celery_from_config(
                    self.app_config, self.global_config,
                    force_celery_always_eager=True)
            else:
                setup_celery_from_config(self.app_config, self.global_config)

        #######################################################
        # Insert appropriate things into mediagoblin.mg_globals
        #
        # certain properties need to be accessed globally eg from
        # validators, etc, which might not access to the request
        # object.
        #
        # Note, we are trying to transition this out;
        # run with environment variable DISABLE_GLOBALS=true
        # to work on it
        #######################################################

        if not DISABLE_GLOBALS:
            setup_globals(app=self)

        # Workbench *currently* only used by celery, so this only
        # matters in always eager mode :)
        self.workbench_manager = setup_workbench()

        # instantiate application meddleware
        self.meddleware = [common.import_component(m)(self)
                           for m in meddleware.ENABLED_MEDDLEWARE]

    @contextmanager
    def gen_context(self, ctx=None, **kwargs):
        """
        Attach contextual information to request, or generate a context object

        This avoids global variables; various utilities and contextual
        information (current translation, etc) are attached to this
        object.
        """
        if DISABLE_GLOBALS:
            with self.db_manager.session_scope() as db:
                yield self._gen_context(db, ctx)
        else:
            yield self._gen_context(self.db, ctx)

    def _gen_context(self, db, ctx, **kwargs):
        # Set up context
        # --------------

        # Is a context provided?
        if ctx is None:
            ctx = Context()
        
        # Attach utilities
        # ----------------

        # Attach self as request.app
        # Also attach a few utilities from request.app for convenience?
        ctx.app = self

        ctx.db = db

        ctx.staticdirect = self.staticdirector

        # Do special things if this is a request
        # --------------------------------------
        if isinstance(ctx, Request):
            ctx = self._request_only_gen_context(ctx)

        return ctx

    def _request_only_gen_context(self, request):
        """
        Requests get some extra stuff attached to them that's not relevant
        otherwise.
        """
        # Do we really want to load this via middleware?  Maybe?
        request.session = self.session_manager.load_session_from_cookie(request)

        request.locale = translate.get_locale_from_request(request)

        # This should be moved over for certain, but how to deal with
        # request.locale?
        request.template_env = template.get_jinja_env(
            self, self.template_loader, request.locale)

        mg_request.setup_user_in_request(request)

        ## Routing / controller loading stuff
        request.map_adapter = self.url_map.bind_to_environ(request.environ)

        def build_proxy(endpoint, **kw):
            try:
                qualified = kw.pop('qualified')
            except KeyError:
                qualified = False

            return request.map_adapter.build(
                    endpoint,
                    values=dict(**kw),
                    force_external=qualified)

        request.urlgen = build_proxy

        return request

    def call_backend(self, environ, start_response):
        request = Request(environ)

        # Compatibility with django, use request.args preferrably
        request.GET = request.args

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
        with self.gen_context(request) as request:
            return self._finish_call_backend(request, environ, start_response)

    def _finish_call_backend(self, request, environ, start_response):
        # Log user out if authentication_disabled
        no_auth_logout(request)

        request.controller_name = None
        try:
            found_rule, url_values = request.map_adapter.match(return_rule=True)
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

        ## TODO: get rid of meddleware, turn it into hooks only
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

        request = hook_transform("modify_request", request)

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

        self.session_manager.save_session_to_cookie(
            request.session,
            request, response)

        return response(environ, start_response)

    def __call__(self, environ, start_response):
        ## If more errors happen that look like unclean sessions:
        # self.db.check_session_clean()

        try:
            return self.call_backend(environ, start_response)
        finally:
            if not DISABLE_GLOBALS:
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
    del app_config['config']

    mgoblin_app = MediaGoblinApp(mediagoblin_config)
    mgoblin_app.call_backend = SharedDataMiddleware(mgoblin_app.call_backend,
                                                    exports=app_config)
    mgoblin_app = hook_transform('wrap_wsgi', mgoblin_app)

    return mgoblin_app


def paste_server_selector(wsgi_app, global_config=None, **app_config):
    """
    Select between gunicorn and paste depending on what ia available
    """
    # See if we can import the gunicorn server...
    # otherwise we'll use the paste server
    try:
        import gunicorn
    except ImportError:
        gunicorn = None

    if gunicorn is None:
        # use paste
        from paste.httpserver import server_runner

        cleaned_app_config = dict(
            [(key, app_config[key])
             for key in app_config
             if key in ["host", "port", "handler", "ssl_pem", "ssl_context",
                        "server_version", "protocol_version", "start_loop",
                        "daemon_threads", "socket_timeout", "use_threadpool",
                        "threadpool_workers", "threadpool_options",
                        "request_queue_size"]])

        return server_runner(wsgi_app, global_config, **cleaned_app_config)
    else:
        # use gunicorn
        from gunicorn.app.pasterapp import PasterServerApplication
        return PasterServerApplication(wsgi_app, global_config, **app_config)
