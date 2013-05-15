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

from mediagoblin.tools import pluginapi
import pkg_resources


def append_to_specific_context(context):
    context['specific_page_append'] = 'in yer specificpage'
    return context

def append_to_global_context(context):
    context['global_append'] = 'globally appended!'
    return context

def double_doubleme(context):
    if 'doubleme' in context:
        context['doubleme'] = context['doubleme'] * 2
    return context


def setup_plugin():
    routes = [
        ('modify_context.specific_page',
         '/modify_context/specific/',
         'mediagoblin.tests.testplugins.modify_context.views:specific'),
        ('modify_context.general_page',
         '/modify_context/',
         'mediagoblin.tests.testplugins.modify_context.views:general')]

    pluginapi.register_routes(routes)
    pluginapi.register_template_path(
        pkg_resources.resource_filename(
            'mediagoblin.tests.testplugins.modify_context', 'templates'))


hooks = {
    'setup': setup_plugin,
    ('modify_context.specific_page',
     'contextplugin/specific.html'): append_to_specific_context,
    'template_global_context': append_to_global_context,
    'template_context_prerender': double_doubleme}
