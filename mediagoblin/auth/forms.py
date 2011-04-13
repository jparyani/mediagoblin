# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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


class RegistrationForm(wtforms.Form):
    username = wtforms.TextField(
        'Username',
        [wtforms.validators.Required(),
         wtforms.validators.Length(min=3, max=30),
         wtforms.validators.Regexp(r'^\w+$')])
    password = wtforms.PasswordField(
        'Password',
        [wtforms.validators.Required(),
         wtforms.validators.Length(min=6, max=30),
         wtforms.validators.EqualTo('confirm_password')])
    confirm_password = wtforms.PasswordField(
        'Confirm password',
        [wtforms.validators.Required()])
    email = wtforms.TextField(
        'Email address',
        [wtforms.validators.Required(),
         wtforms.validators.Email()])


class LoginForm(wtforms.Form):
    username = wtforms.TextField(
        'Username',
        [wtforms.validators.Required(),
         wtforms.validators.Regexp(r'^\w+$')])
    password = wtforms.PasswordField(
        'Password',
        [wtforms.validators.Required()])
