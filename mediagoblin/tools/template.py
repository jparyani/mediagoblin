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


import jinja2
from jinja2.ext import Extension
from jinja2.nodes import Include, Const

from babel.localedata import exists
from werkzeug.urls import url_quote_plus

from mediagoblin import mg_globals
from mediagoblin import messages
from mediagoblin import _version
from mediagoblin.tools import common
from mediagoblin.tools.translate import is_rtl
from mediagoblin.tools.translate import set_thread_locale
from mediagoblin.tools.translate import get_locale_from_request
from mediagoblin.tools.pluginapi import get_hook_templates, hook_transform
from mediagoblin.tools.timesince import timesince
from mediagoblin.meddleware.csrf import render_csrf_form_token


SETUP_JINJA_ENVS = {}


def get_jinja_env(template_loader, locale):
    """
    Set up the Jinja environment,

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    set_thread_locale(locale)

    # If we have a jinja environment set up with this locale, just
    # return that one.
    if locale in SETUP_JINJA_ENVS:
        return SETUP_JINJA_ENVS[locale]

    # The default config does not require a [jinja2] block.
    # You may create one if you wish to enable additional jinja2 extensions,
    # see example in config_spec.ini 
    jinja2_config = mg_globals.global_config.get('jinja2', {})
    local_exts = jinja2_config.get('extensions', [])

    # jinja2.StrictUndefined will give exceptions on references
    # to undefined/unknown variables in templates.
    template_env = jinja2.Environment(
        loader=template_loader, autoescape=True,
        undefined=jinja2.StrictUndefined,
        extensions=[
            'jinja2.ext.i18n', 'jinja2.ext.autoescape',
            TemplateHookExtension] + local_exts)

    template_env.install_gettext_callables(
        mg_globals.thread_scope.translations.ugettext,
        mg_globals.thread_scope.translations.ungettext)

    # All templates will know how to ...
    # ... fetch all waiting messages and remove them from the queue
    # ... construct a grid of thumbnails or other media
    # ... have access to the global and app config
    # ... determine if the language is rtl or ltr
    template_env.globals['fetch_messages'] = messages.fetch_messages
    template_env.globals['app_config'] = mg_globals.app_config
    template_env.globals['global_config'] = mg_globals.global_config
    template_env.globals['version'] = _version.__version__
    template_env.globals['auth'] = mg_globals.app.auth
    template_env.globals['is_rtl'] = is_rtl(locale)
    template_env.filters['urlencode'] = url_quote_plus

    # add human readable fuzzy date time
    template_env.globals['timesince'] = timesince

    # allow for hooking up plugin templates
    template_env.globals['get_hook_templates'] = get_hook_templates

    template_env.globals = hook_transform(
        'template_global_context', template_env.globals)

    #### THIS IS TEMPORARY, PLEASE FIX IT
    ## Notifications stuff is not yet a plugin (and we're not sure it will be),
    ## but it needs to add stuff to the context.  This is THE WRONG WAY TO DO IT
    from mediagoblin import notifications
    template_env.globals['get_notifications'] = notifications.get_notifications
    template_env.globals[
        'get_notification_count'] = notifications.get_notification_count
    template_env.globals[
        'get_comment_subscription'] = notifications.get_comment_subscription

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

    # allow plugins to do things to the context
    if request.controller_name:
        context = hook_transform(
            (request.controller_name, template_path),
            context)

    # More evil: allow plugins to possibly do something to the context
    # in every request ever with access to the request and other
    # variables.  Note: this is slower than using
    # template_global_context
    context = hook_transform(
        'template_context_prerender', context)

    rendered = template.render(context)

    if common.TESTS_ENABLED:
        TEMPLATE_TEST_CONTEXT[template_path] = context

    return rendered


def clear_test_template_context():
    global TEMPLATE_TEST_CONTEXT
    TEMPLATE_TEST_CONTEXT = {}


class TemplateHookExtension(Extension):
    """
    Easily loop through a bunch of templates from a template hook.

    Use:
      {% template_hook("comment_extras") %}

    ... will include all templates hooked into the comment_extras section.
    """

    tags = set(["template_hook"])

    def parse(self, parser):
        includes = []
        expr = parser.parse_expression()
        lineno = expr.lineno
        hook_name = expr.args[0].value

        for template_name in get_hook_templates(hook_name):
            includes.append(
                parser.parse_import_context(
                    Include(Const(template_name), True, False, lineno=lineno),
                    True))

        return includes
