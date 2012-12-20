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

from math import ceil
import jinja2
from babel.localedata import exists
from werkzeug.urls import url_quote_plus

from mediagoblin import mg_globals
from mediagoblin import messages
from mediagoblin.tools import common
from mediagoblin.tools.translate import get_gettext_translation
from mediagoblin.meddleware.csrf import render_csrf_form_token


SETUP_JINJA_ENVS = {}


def get_jinja_env(template_loader, locale):
    """
    Set up the Jinja environment,

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    mg_globals.thread_scope.translations = get_gettext_translation(locale)

    # If we have a jinja environment set up with this locale, just
    # return that one.
    if SETUP_JINJA_ENVS.has_key(locale):
        return SETUP_JINJA_ENVS[locale]

    # jinja2.StrictUndefined will give exceptions on references
    # to undefined/unknown variables in templates.
    template_env = jinja2.Environment(
        loader=template_loader, autoescape=True,
        undefined=jinja2.StrictUndefined,
        extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'])

    template_env.install_gettext_callables(
        mg_globals.thread_scope.translations.ugettext,
        mg_globals.thread_scope.translations.ungettext)

    # All templates will know how to ...
    # ... fetch all waiting messages and remove them from the queue
    # ... construct a grid of thumbnails or other media
    # ... have access to the global and app config
    template_env.globals['fetch_messages'] = messages.fetch_messages
    template_env.globals['app_config'] = mg_globals.app_config
    template_env.globals['global_config'] = mg_globals.global_config

    template_env.filters['urlencode'] = url_quote_plus

    if exists(locale):
        SETUP_JINJA_ENVS[locale] = template_env

    return template_env


# We'll store context information here when doing unit tests
TEMPLATE_TEST_CONTEXT = {}


def render_template(request, template_path, context):
    """
    Render a template with context.

    Always inserts the request into the context, so you don't have to.
    Also stores the context if we're doing unit tests.  Helpful!
    """
    template = request.template_env.get_template(
        template_path)
    context['request'] = request
    rendered_csrf_token = render_csrf_form_token(request)
    if rendered_csrf_token is not None:
        context['csrf_token'] = render_csrf_form_token(request)
    rendered = template.render(context)

    if common.TESTS_ENABLED:
        TEMPLATE_TEST_CONTEXT[template_path] = context

    return rendered


def clear_test_template_context():
    global TEMPLATE_TEST_CONTEXT
    TEMPLATE_TEST_CONTEXT = {}
