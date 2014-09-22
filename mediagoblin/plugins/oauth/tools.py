# -*- coding: utf-8 -*-
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

import uuid

from random import getrandbits

from datetime import datetime

from functools import wraps

import six

from mediagoblin.tools.response import json_response


def require_client_auth(controller):
    '''
    View decorator

    - Requires the presence of ``?client_id``
    '''
    # Avoid circular import
    from mediagoblin.plugins.oauth.models import OAuthClient

    @wraps(controller)
    def wrapper(request, *args, **kw):
        if not request.GET.get('client_id'):
            return json_response({
                'status': 400,
                'errors': [u'No client identifier in URL']},
                _disable_cors=True)

        client = OAuthClient.query.filter(
                OAuthClient.identifier == request.GET.get('client_id')).first()

        if not client:
            return json_response({
                'status': 400,
                'errors': [u'No such client identifier']},
                _disable_cors=True)

        return controller(request, client)

    return wrapper


def create_token(client, user):
    '''
    Create an OAuthToken and an OAuthRefreshToken entry in the database

    Returns the data structure expected by the OAuth clients.
    '''
    from mediagoblin.plugins.oauth.models import OAuthToken, OAuthRefreshToken

    token = OAuthToken()
    token.user = user
    token.client = client
    token.save()

    refresh_token = OAuthRefreshToken()
    refresh_token.user = user
    refresh_token.client = client
    refresh_token.save()

    # expire time of token in full seconds
    # timedelta.total_seconds is python >= 2.7 or we would use that
    td = token.expires - datetime.now()
    exp_in = 86400*td.days + td.seconds # just ignore µsec

    return {'access_token': token.token, 'token_type': 'bearer',
            'refresh_token': refresh_token.token, 'expires_in': exp_in}


def generate_identifier():
    ''' Generates a ``uuid.uuid4()`` '''
    return six.text_type(uuid.uuid4())


def generate_token():
    ''' Uses generate_identifier '''
    return generate_identifier()


def generate_refresh_token():
    ''' Uses generate_identifier '''
    return generate_identifier()


def generate_code():
    ''' Uses generate_identifier '''
    return generate_identifier()


def generate_secret():
    '''
    Generate a long string of pseudo-random characters
    '''
    # XXX: We might not want it to use bcrypt, since bcrypt takes its time to
    # generate the result.
    return six.text_type(getrandbits(192))

