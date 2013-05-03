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

import forms as auth_forms
from mediagoblin.auth import lib as auth_lib
from mediagoblin.db.models import User
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools import pluginapi
from sqlalchemy import or_


PLUGIN_DIR = os.path.dirname(__file__)


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.pluginapi.basic_auth')


def check_login(user, login_form):
    return user.check_login(login_form.password.data)


def get_user(login_form):
    username = login_form.data['username']
    user = User.query.filter(
        or_(
            User.username == username,
            User.email == username,
        )).first()
    return user


def create_user(registration_form):
    user = User()
    user.username = registration_form.data['username']
    user.email = registration_form.data['email']
    user.pw_hash = auth_lib.bcrypt_gen_password_hash(
        registration_form.password.data)
    user.verification_key = unicode(uuid.uuid4())
    user.save()
    return user


def extra_validation(register_form, *args):
    users_with_username = User.query.filter_by(
        username=register_form.data['username']).count()
    users_with_email = User.query.filter_by(
        email=register_form.data['email']).count()

    extra_validation_passes = True

    if users_with_username:
        register_form.username.errors.append(
            _(u'Sorry, a user with that name already exists.'))
        extra_validation_passes = False
    if users_with_email:
        register_form.email.errors.append(
            _(u'Sorry, a user with that email address already exists.'))
        extra_validation_passes = False

    return extra_validation_passes


def get_login_form(request):
    return auth_forms.LoginForm(request.form)


def get_registration_form(request):
    return auth_forms.RegistrationForm(request.form)


hooks = {
    'setup': setup_plugin,
    'auth_check_login': check_login,
    'auth_get_user': get_user,
    'auth_create_user': create_user,
    'auth_extra_validation': extra_validation,
    'auth_get_login_form': get_login_form,
    'auth_get_registration_form': get_registration_form,
}
