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
import wtforms

from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.auth.tools import normalize_user_or_email_field


class RegistrationForm(wtforms.Form):
    username = wtforms.TextField(
        _('Username'),
        [wtforms.validators.InputRequired(),
         normalize_user_or_email_field(allow_email=False)])
    password = wtforms.PasswordField(
        _('Password'),
        [wtforms.validators.InputRequired(),
         wtforms.validators.Length(min=5, max=1024)])
    email = wtforms.TextField(
        _('Email address'),
        [wtforms.validators.InputRequired(),
         normalize_user_or_email_field(allow_user=False)])


class LoginForm(wtforms.Form):
    username = wtforms.TextField(
        _('Username or Email'),
        [wtforms.validators.InputRequired(),
         normalize_user_or_email_field()])
    password = wtforms.PasswordField(
        _('Password'))
    stay_logged_in = wtforms.BooleanField(
        label='',
        description=_('Stay logged in'))


class ForgotPassForm(wtforms.Form):
    username = wtforms.TextField(
        _('Username or email'),
        [wtforms.validators.InputRequired(),
         normalize_user_or_email_field()])


class ChangeForgotPassForm(wtforms.Form):
    password = wtforms.PasswordField(
        'Password',
        [wtforms.validators.InputRequired(),
         wtforms.validators.Length(min=5, max=1024)])
    token = wtforms.HiddenField(
        '',
        [wtforms.validators.InputRequired()])


class ChangePassForm(wtforms.Form):
    old_password = wtforms.PasswordField(
        _('Old password'),
        [wtforms.validators.InputRequired()],
        description=_(
            "Enter your old password to prove you own this account."))
    new_password = wtforms.PasswordField(
        _('New password'),
        [wtforms.validators.InputRequired(),
         wtforms.validators.Length(min=6, max=30)],
        id="password")
