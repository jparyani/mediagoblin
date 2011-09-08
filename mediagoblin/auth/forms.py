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

import wtforms
import re

from mediagoblin.util import fake_ugettext_passthrough as _


class RegistrationForm(wtforms.Form):
    username = wtforms.TextField(
        _('Username'),
        [wtforms.validators.Required(),
         wtforms.validators.Length(min=3, max=30),
         wtforms.validators.Regexp(r'^\w+$')])
    password = wtforms.PasswordField(
        _('Password'),
        [wtforms.validators.Required(),
         wtforms.validators.Length(min=6, max=30),
         wtforms.validators.EqualTo(
                'confirm_password',
                _('Passwords must match.'))])
    confirm_password = wtforms.PasswordField(
        _('Confirm password'),
        [wtforms.validators.Required()],
        description=_(
            u"Type it again here to make sure there are no spelling mistakes."))
    email = wtforms.TextField(
        _('Email address'),
        [wtforms.validators.Required(),
         wtforms.validators.Email()])


class LoginForm(wtforms.Form):
    username = wtforms.TextField(
        _('Username'),
        [wtforms.validators.Required(),
         wtforms.validators.Regexp(r'^\w+$')])
    password = wtforms.PasswordField(
        _('Password'),
        [wtforms.validators.Required()])


class ForgotPassForm(wtforms.Form):
    username = wtforms.TextField(
        'Username or email',
        [wtforms.validators.Required()])

    def validate_username(form,field):
        if not (re.match(r'^\w+$',field.data) or
               re.match(r'^.+@[^.].*\.[a-z]{2,10}$',field.data, re.IGNORECASE)):
            raise wtforms.ValidationError(u'Incorrect input')


class ChangePassForm(wtforms.Form):
    password = wtforms.PasswordField(
        'Password',
        [wtforms.validators.Required(),
         wtforms.validators.Length(min=6, max=30),
         wtforms.validators.EqualTo(
                'confirm_password',
                'Passwords must match.')])
    confirm_password = wtforms.PasswordField(
        'Confirm password',
        [wtforms.validators.Required()])
    userid = wtforms.HiddenField(
        '',
        [wtforms.validators.Required()])
    token = wtforms.HiddenField(
        '',
        [wtforms.validators.Required()])

