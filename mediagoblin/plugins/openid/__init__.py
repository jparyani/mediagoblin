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
import uuid

from sqlalchemy import or_

from mediagoblin.auth.tools import create_basic_user
from mediagoblin.db.models import User
from mediagoblin.plugins.openid.models import OpenIDUserURL
from mediagoblin.tools import pluginapi
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

PLUGIN_DIR = os.path.dirname(__file__)


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.plugins.openid')

    routes = [
        ('mediagoblin.plugins.openid.register',
         '/auth/openid/register/',
         'mediagoblin.plugins.openid.views:register'),
        ('mediagoblin.plugins.openid.login',
         '/auth/openid/login/',
         'mediagoblin.plugins.openid.views:login'),
        ('mediagoblin.plugins.openid.finish_login',
         '/auth/openid/login/finish/',
         'mediagoblin.plugins.openid.views:finish_login'),
        ('mediagoblin.plugins.openid.edit',
         '/edit/openid/',
         'mediagoblin.plugins.openid.views:start_edit'),
        ('mediagoblin.plugins.openid.finish_edit',
         '/edit/openid/finish/',
         'mediagoblin.plugins.openid.views:finish_edit'),
        ('mediagoblin.plugins.openid.delete',
         '/edit/openid/delete/',
         'mediagoblin.plugins.openid.views:delete_openid'),
        ('mediagoblin.plugins.openid.finish_delete',
         '/edit/openid/delete/finish/',
         'mediagoblin.plugins.openid.views:finish_delete')]

    pluginapi.register_routes(routes)
    pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))

    pluginapi.register_template_hooks(
        {'register_link': 'mediagoblin/plugins/openid/register_link.html',
         'login_link': 'mediagoblin/plugins/openid/login_link.html',
         'edit_link': 'mediagoblin/plugins/openid/edit_link.html'})


def create_user(register_form):
    if 'openid' in register_form:
        username = register_form.username.data
        user = User.query.filter(
            or_(
                User.username == username,
                User.email == username,
            )).first()

        if not user:
            user = create_basic_user(register_form)

        new_entry = OpenIDUserURL()
        new_entry.openid_url = register_form.openid.data
        new_entry.user_id = user.id
        new_entry.save()

        return user


def extra_validation(register_form):
    openid = register_form.openid.data if 'openid' in \
        register_form else None
    if openid:
        openid_url_exists = OpenIDUserURL.query.filter_by(
            openid_url=openid
            ).count()

        extra_validation_passes = True

        if openid_url_exists:
            register_form.openid.errors.append(
                _('Sorry, an account is already registered to that OpenID.'))
            extra_validation_passes = False

        return extra_validation_passes


def no_pass_redirect():
    return 'openid'


def add_to_form_context(context):
    context['openid_link'] = True
    return context


def Auth():
    return True

hooks = {
    'setup': setup_plugin,
    'authentication': Auth,
    'auth_extra_validation': extra_validation,
    'auth_create_user': create_user,
    'auth_no_pass_redirect': no_pass_redirect,
    ('mediagoblin.auth.register',
     'mediagoblin/auth/register.html'): add_to_form_context,
}
