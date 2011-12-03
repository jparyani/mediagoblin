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

from math import ceil
import jinja2
from babel.localedata import exists
from mediagoblin import mg_globals
from mediagoblin import messages
from mediagoblin.tools import common
from mediagoblin.tools.translate import setup_gettext
from mediagoblin.meddleware.csrf import render_csrf_form_token


SETUP_JINJA_ENVS = {}


def get_jinja_env(template_loader, locale):
    """
    Set up the Jinja environment,

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    setup_gettext(locale)

    # If we have a jinja environment set up with this locale, just
    # return that one.
    if SETUP_JINJA_ENVS.has_key(locale):
        return SETUP_JINJA_ENVS[locale]

    template_env = jinja2.Environment(
        loader=template_loader, autoescape=True,
        extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'])

    template_env.install_gettext_callables(
        mg_globals.translations.ugettext,
        mg_globals.translations.ungettext)

    # All templates will know how to ...
    # ... fetch all waiting messages and remove them from the queue
    # ... construct a grid of thumbnails or other media
    # ... have access to the global and app config
    template_env.globals['fetch_messages'] = messages.fetch_messages
    template_env.globals['gridify_list'] = gridify_list
    template_env.globals['gridify_cursor'] = gridify_cursor
    template_env.globals['app_config'] = mg_globals.app_config
    template_env.globals['global_config'] = mg_globals.global_config

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


def gridify_list(this_list, num_cols=5):
    """
    Generates a list of lists where each sub-list's length depends on
    the number of columns in the list
    """
    grid = []

    # Figure out how many rows we should have
    num_rows = int(ceil(float(len(this_list)) / num_cols))

    for row_num in range(num_rows):
        slice_min = row_num * num_cols
        slice_max = (row_num + 1) * num_cols

        row = this_list[slice_min:slice_max]

        grid.append(row)

    return grid


def gridify_cursor(this_cursor, num_cols=5):
    """
    Generates a list of lists where each sub-list's length depends on
    the number of columns in the list
    """
    return gridify_list(list(this_cursor), num_cols)
