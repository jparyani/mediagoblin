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
import json

from webob import exc, Response
from urllib import urlencode
from uuid import uuid4
from datetime import datetime
from functools import wraps

from mediagoblin.tools import pluginapi
from mediagoblin.tools.response import render_to_response
from mediagoblin.decorators import require_active_login
from mediagoblin.messages import add_message, SUCCESS, ERROR
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.plugins.oauth.models import OAuthCode, OAuthToken

_log = logging.getLogger(__name__)


@require_active_login
def authorize(request):
    # TODO: Check if allowed

    # Client is allowed by the user
    if True or already_authorized:
        # Generate a code
        # Save the code, the client will later use it to obtain an access token
        # Redirect the user agent to the redirect_uri with the code

        if not 'redirect_uri' in request.GET:
            add_message(request, ERROR, _('No redirect_uri found'))

        code = OAuthCode()
        code.code = unicode(uuid4())
        code.user = request.user
        code.save()

        redirect_uri = ''.join([
            request.GET.get('redirect_uri'),
            '?',
            urlencode({'code': code.code})])

        _log.debug('Redirecting to {0}'.format(redirect_uri))

        return exc.HTTPFound(location=redirect_uri)
    else:
        # Show prompt to allow client to access data
        # - on accept: send the user agent back to the redirect_uri with the
        # code parameter
        # - on deny: send the user agent back to the redirect uri with error
        # information
        pass
    return render_to_response(request, 'oauth/base.html', {})


def access_token(request):
    if request.GET.get('code'):
        code = OAuthCode.query.filter(OAuthCode.code == request.GET.get('code'))\
                .first()

        if code:
            token = OAuthToken()
            token.token = unicode(uuid4())
            token.user = code.user
            token.save()

            access_token_data = {
                'access_token': token.token,
                'token_type': 'what_do_i_use_this_for',  # TODO
                'expires_in':
                (token.expires - datetime.now()).total_seconds(),
                'refresh_token': 'This should probably be safe'}
            return Response(json.dumps(access_token_data))

    error_data = {
        'error': 'Incorrect code'}
    return Response(json.dumps(error_data))
