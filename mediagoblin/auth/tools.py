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
from sqlalchemy import or_

from mediagoblin import mg_globals
from mediagoblin.auth import lib as auth_lib
from mediagoblin.db.models import User
from mediagoblin.tools.mail import normalize_email, send_email
from mediagoblin.tools.template import render_template
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

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


EMAIL_VERIFICATION_TEMPLATE = (
    u"http://{host}{uri}?"
    u"userid={userid}&token={verification_key}")


def send_verification_email(user, request):
    """
    Send the verification email to users to activate their accounts.

    Args:
    - user: a user object
    - request: the request
    """
    rendered_email = render_template(
        request, 'mediagoblin/auth/verification_email.txt',
        {'username': user.username,
         'verification_url': EMAIL_VERIFICATION_TEMPLATE.format(
                host=request.host,
                uri=request.urlgen('mediagoblin.auth.verify_email'),
                userid=unicode(user.id),
                verification_key=user.verification_key)})

    # TODO: There is no error handling in place
    send_email(
        mg_globals.app_config['email_sender_address'],
        [user.email],
        # TODO
        # Due to the distributed nature of GNU MediaGoblin, we should
        # find a way to send some additional information about the
        # specific GNU MediaGoblin instance in the subject line. For
        # example "GNU MediaGoblin @ Wandborg - [...]".
        'GNU MediaGoblin - Verify your email!',
        rendered_email)


def check_login_simple(username, password, username_might_be_email=False):
    search = (User.username == username)
    if username_might_be_email and ('@' in username):
        search = or_(search, User.email == username)
    user = User.query.filter(search).first()
    if not user:
        _log.info("User %r not found", username)
        auth_lib.fake_login_attempt()
        return None
    if not auth_lib.bcrypt_check_password(password, user.pw_hash):
        _log.warn("Wrong password for %r", username)
        return None
    _log.info("Logging %r in", username)
    return user
