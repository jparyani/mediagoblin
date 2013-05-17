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

import logging
import wtforms

from mediagoblin import mg_globals
from mediagoblin.tools.mail import normalize_email
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.tools.pluginapi import hook_handle

_log = logging.getLogger(__name__)


def normalize_user_or_email_field(allow_email=True, allow_user=True):
    """
    Check if we were passed a field that matches a username and/or email
    pattern.

    This is useful for fields that can take either a username or email
    address. Use the parameters if you want to only allow a username for
    instance"""
    message = _(u'Invalid User name or email address.')
    nomail_msg = _(u"This field does not take email addresses.")
    nouser_msg = _(u"This field requires an email address.")

    def _normalize_field(form, field):
        email = u'@' in field.data
        if email:  # normalize email address casing
            if not allow_email:
                raise wtforms.ValidationError(nomail_msg)
            wtforms.validators.Email()(form, field)
            field.data = normalize_email(field.data)
        else:  # lower case user names
            if not allow_user:
                raise wtforms.ValidationError(nouser_msg)
            wtforms.validators.Length(min=3, max=30)(form, field)
            wtforms.validators.Regexp(r'^\w+$')(form, field)
            field.data = field.data.lower()
        if field.data is None:  # should not happen, but be cautious anyway
            raise wtforms.ValidationError(message)
    return _normalize_field


class AuthError(Exception):
    def __init__(self):
        self.value = 'No Authentication Plugin is enabled and no_auth = false'\
                     ' in config!'

    def __str__(self):
        return repr(self.value)


def check_auth_enabled():
    no_auth = mg_globals.app_config['no_auth']
    auth_plugin = True if hook_handle('authentication') is not None else False

    if no_auth == 'false' and not auth_plugin:
        raise AuthError

    if no_auth == 'true' and not auth_plugin:
        _log.warning('No authentication is enabled')
        return False
    else:
        return True


def no_auth_logout(request):
    """Log out the user if in no_auth mode"""
    if not mg_globals.app.auth:
        request.session.delete()
