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
from pkg_resources import resource_filename
import os

from sqlalchemy import or_

from mediagoblin.auth.tools import create_basic_user
from mediagoblin.db.models import User
from mediagoblin.plugins.persona.models import PersonaUserEmails
from mediagoblin.tools import pluginapi
from mediagoblin.tools.staticdirect import PluginStatic
from mediagoblin.tools.translate import pass_to_ugettext as _

PLUGIN_DIR = os.path.dirname(__file__)


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.plugins.persona')

    routes = [
        ('mediagoblin.plugins.persona.login',
         '/auth/persona/login/',
         'mediagoblin.plugins.persona.views:login'),
        ('mediagoblin.plugins.persona.register',
         '/auth/persona/register/',
         'mediagoblin.plugins.persona.views:register'),
        ('mediagoblin.plugins.persona.edit',
         '/edit/persona/',
         'mediagoblin.plugins.persona.views:edit'),
        ('mediagoblin.plugins.persona.add',
         '/edit/persona/add/',
         'mediagoblin.plugins.persona.views:add')]

    pluginapi.register_routes(routes)
    pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))
    pluginapi.register_template_hooks(
        {'persona_head': 'mediagoblin/plugins/persona/persona_js_head.html',
         'persona_form': 'mediagoblin/plugins/persona/persona.html',
         'edit_link': 'mediagoblin/plugins/persona/edit_link.html',
         'login_link': 'mediagoblin/plugins/persona/login_link.html',
         'register_link': 'mediagoblin/plugins/persona/register_link.html'})


def create_user(register_form):
    if 'persona_email' in register_form:
        username = register_form.username.data
        user = User.query.filter(
            or_(
                User.username == username,
                User.email == username,
            )).first()

        if not user:
            user = create_basic_user(register_form)

        new_entry = PersonaUserEmails()
        new_entry.persona_email = register_form.persona_email.data
        new_entry.user_id = user.id
        new_entry.save()

        return user


def extra_validation(register_form):
    persona_email = register_form.persona_email.data if 'persona_email' in \
        register_form else None
    if persona_email:
        persona_email_exists = PersonaUserEmails.query.filter_by(
            persona_email=persona_email
            ).count()

        extra_validation_passes = True

        if persona_email_exists:
            register_form.persona_email.errors.append(
                _('Sorry, an account is already registered to that Persona'
                  ' email.'))
            extra_validation_passes = False

        return extra_validation_passes


def Auth():
    return True


def add_to_global_context(context):
    if len(pluginapi.hook_runall('authentication')) == 1:
        context['persona_auth'] = True
    context['persona'] = True
    return context

hooks = {
    'setup': setup_plugin,
    'authentication': Auth,
    'auth_extra_validation': extra_validation,
    'auth_create_user': create_user,
    'template_global_context': add_to_global_context,
    'static_setup': lambda: PluginStatic(
        'coreplugin_persona',
        resource_filename('mediagoblin.plugins.persona', 'static'))
}
