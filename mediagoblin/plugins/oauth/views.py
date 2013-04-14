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

import logging

from urllib import urlencode

from werkzeug.exceptions import BadRequest

from mediagoblin.tools.response import render_to_response, redirect
from mediagoblin.decorators import require_active_login
from mediagoblin.messages import add_message, SUCCESS
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.plugins.oauth.models import OAuthCode, OAuthClient, \
        OAuthUserClient, OAuthRefreshToken
from mediagoblin.plugins.oauth.forms import ClientRegistrationForm, \
        AuthorizationForm
from mediagoblin.plugins.oauth.tools import require_client_auth, \
        create_token
from mediagoblin.plugins.api.tools import json_response

_log = logging.getLogger(__name__)


@require_active_login
def register_client(request):
    '''
    Register an OAuth client
    '''
    form = ClientRegistrationForm(request.form)

    if request.method == 'POST' and form.validate():
        client = OAuthClient()
        client.name = unicode(form.name.data)
        client.description = unicode(form.description.data)
        client.type = unicode(form.type.data)
        client.owner_id = request.user.id
        client.redirect_uri = unicode(form.redirect_uri.data)

        client.save()

        add_message(request, SUCCESS, _('The client {0} has been registered!')\
                .format(
                    client.name))

        return redirect(request, 'mediagoblin.plugins.oauth.list_clients')

    return render_to_response(
            request,
            'oauth/client/register.html',
            {'form': form})


@require_active_login
def list_clients(request):
    clients = request.db.OAuthClient.query.filter(
            OAuthClient.owner_id == request.user.id).all()
    return render_to_response(request, 'oauth/client/list.html',
            {'clients': clients})


@require_active_login
def list_connections(request):
    connections = OAuthUserClient.query.filter(
            OAuthUserClient.user == request.user).all()
    return render_to_response(request, 'oauth/client/connections.html',
            {'connections': connections})


@require_active_login
def authorize_client(request):
    form = AuthorizationForm(request.form)

    client = OAuthClient.query.filter(OAuthClient.id ==
        form.client_id.data).first()

    if not client:
        _log.error('No such client id as received from client authorization \
form.')
        raise BadRequest()

    if form.validate():
        relation = OAuthUserClient()
        relation.user_id = request.user.id
        relation.client_id = form.client_id.data
        if form.allow.data:
            relation.state = u'approved'
        elif form.deny.data:
            relation.state = u'rejected'
        else:
            raise BadRequest()

        relation.save()

        return redirect(request, location=form.next.data)

    return render_to_response(
        request,
        'oauth/authorize.html',
        {'form': form,
            'client': client})


@require_client_auth
@require_active_login
def authorize(request, client):
    # TODO: Get rid of the JSON responses in this view, it's called by the
    # user-agent, not the client.
    user_client_relation = OAuthUserClient.query.filter(
            (OAuthUserClient.user == request.user)
            & (OAuthUserClient.client == client))

    if user_client_relation.filter(OAuthUserClient.state ==
            u'approved').count():
        redirect_uri = None

        if client.type == u'public':
            if not client.redirect_uri:
                return json_response({
                    'status': 400,
                    'errors':
                        [u'Public clients should have a redirect_uri pre-set.']},
                        _disable_cors=True)

            redirect_uri = client.redirect_uri

        if client.type == u'confidential':
            redirect_uri = request.GET.get('redirect_uri', client.redirect_uri)
            if not redirect_uri:
                return json_response({
                    'status': 400,
                    'errors': [u'No redirect_uri supplied!']},
                    _disable_cors=True)

        code = OAuthCode()
        code.user = request.user
        code.client = client
        code.save()

        redirect_uri = ''.join([
            redirect_uri,
            '?',
            urlencode({'code': code.code})])

        _log.debug('Redirecting to {0}'.format(redirect_uri))

        return redirect(request, location=redirect_uri)
    else:
        # Show prompt to allow client to access data
        # - on accept: send the user agent back to the redirect_uri with the
        # code parameter
        # - on deny: send the user agent back to the redirect uri with error
        # information
        form = AuthorizationForm(request.form)
        form.client_id.data = client.id
        form.next.data = request.url
        return render_to_response(
                request,
                'oauth/authorize.html',
                {'form': form,
                'client': client})


def access_token(request):
    '''
    Access token endpoint provides access tokens to any clients that have the
    right grants/credentials
    '''

    client = None
    user = None

    if request.GET.get('code'):
        # Validate the code arg, then get the client object from the db.
        code = OAuthCode.query.filter(OAuthCode.code ==
                request.GET.get('code')).first()

        if not code:
            return json_response({
                'error': 'invalid_request',
                'error_description':
                    'Invalid code.'})

        client = code.client
        user = code.user

    elif request.args.get('refresh_token'):
        # Validate a refresh token, then get the client object from the db.
        refresh_token = OAuthRefreshToken.query.filter(
            OAuthRefreshToken.token ==
            request.args.get('refresh_token')).first()

        if not refresh_token:
            return json_response({
                'error': 'invalid_request',
                'error_description':
                    'Invalid refresh token.'})

        client = refresh_token.client
        user = refresh_token.user

    if client:
        client_identifier = request.GET.get('client_id')

        if not client_identifier:
            return json_response({
                'error': 'invalid_request',
                'error_description':
                    'Missing client_id in request.'})

        if not client_identifier == client.identifier:
            return json_response({
                'error': 'invalid_client',
                'error_description':
                    'Mismatching client credentials.'})

        if client.type == u'confidential':
            client_secret = request.GET.get('client_secret')

            if not client_secret:
                return json_response({
                    'error': 'invalid_request',
                    'error_description':
                        'Missing client_secret in request.'})

            if not client_secret == client.secret:
                return json_response({
                    'error': 'invalid_client',
                    'error_description':
                        'Mismatching client credentials.'})


        access_token_data = create_token(client, user)

        return json_response(access_token_data, _disable_cors=True)

    return json_response({
        'error': 'invalid_request',
        'error_description':
            'Missing `code` or `refresh_token` parameter in request.'})
