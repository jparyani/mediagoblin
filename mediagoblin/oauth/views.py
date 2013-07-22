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

import datetime

from oauthlib.oauth1 import (RequestTokenEndpoint, AuthorizationEndpoint,
                             AccessTokenEndpoint)
                             
from mediagoblin.decorators import require_active_login
from mediagoblin.tools.translate import pass_to_ugettext
from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.tools.request import decode_request
from mediagoblin.tools.response import (render_to_response, redirect, 
                                        json_response, render_400,
                                        form_response)
from mediagoblin.tools.crypto import random_string
from mediagoblin.tools.validator import validate_email, validate_url
from mediagoblin.oauth.forms import AuthorizeForm
from mediagoblin.oauth.oauth import GMGRequestValidator, GMGRequest
from mediagoblin.oauth.tools.request import decode_authorization_header
from mediagoblin.oauth.tools.forms import WTFormData
from mediagoblin.db.models import NonceTimestamp, Client, RequestToken

# possible client types
client_types = ["web", "native"] # currently what pump supports

@csrf_exempt
def client_register(request):
    """ Endpoint for client registration """
    try:
        data = decode_request(request) 
    except ValueError:
        error = "Could not decode data."
        return json_response({"error": error}, status=400)

    if data is "":
        error = "Unknown Content-Type"
        return json_response({"error": error}, status=400)

    if "type" not in data:
        error = "No registration type provided."
        return json_response({"error": error}, status=400)
    if data.get("application_type", None) not in client_types:
        error = "Unknown application_type."
        return json_response({"error": error}, status=400)
    
    client_type = data["type"]

    if client_type == "client_update":
        # updating a client
        if "client_id" not in data:
            error = "client_id is requried to update."
            return json_response({"error": error}, status=400)
        elif "client_secret" not in data:
            error = "client_secret is required to update."
            return json_response({"error": error}, status=400)

        client = Client.query.filter_by(
                id=data["client_id"], 
                secret=data["client_secret"]
                ).first()

        if client is None:
            error = "Unauthorized."
            return json_response({"error": error}, status=403)

        client.application_name = data.get(
                "application_name", 
                client.application_name
                )

        client.application_type = data.get(
                "application_type",
                client.application_type
                )

        app_name = ("application_type", client.application_name)
        if app_name in client_types:
            client.application_name = app_name

    elif client_type == "client_associate":
        # registering
        if "client_id" in data:
            error = "Only set client_id for update."
            return json_response({"error": error}, status=400)
        elif "access_token" in data:
            error = "access_token not needed for registration."
            return json_response({"error": error}, status=400)
        elif "client_secret" in data:
            error = "Only set client_secret for update."
            return json_response({"error": error}, status=400)

        # generate the client_id and client_secret
        client_id = random_string(22) # seems to be what pump uses
        client_secret = random_string(43) # again, seems to be what pump uses
        expirey = 0 # for now, lets not have it expire
        expirey_db = None if expirey == 0 else expirey
        application_type = data["application_type"] 
 
        # save it
        client = Client(
                id=client_id, 
                secret=client_secret, 
                expirey=expirey_db,
                application_type=application_type,
                )

    else:
        error = "Invalid registration type"
        return json_response({"error": error}, status=400)

    logo_url = data.get("logo_url", client.logo_url)
    if logo_url is not None and not validate_url(logo_url):
        error = "Logo URL {0} is not a valid URL.".format(logo_url)
        return json_response(
                {"error": error}, 
                status=400
                )
    else:
        client.logo_url = logo_url
    
    client.application_name = data.get("application_name", None)

    contacts = data.get("contacts", None)
    if contacts is not None:
        if type(contacts) is not unicode:
            error = "Contacts must be a string of space-seporated email addresses."
            return json_response({"error": error}, status=400)

        contacts = contacts.split()
        for contact in contacts:
            if not validate_email(contact):
                # not a valid email
                error = "Email {0} is not a valid email.".format(contact)
                return json_response({"error": error}, status=400)
     
        
        client.contacts = contacts

    redirect_uris = data.get("redirect_uris", None)
    if redirect_uris is not None:
        if type(redirect_uris) is not unicode:
            error = "redirect_uris must be space-seporated URLs."
            return json_response({"error": error}, status=400)

        redirect_uris = redirect_uris.split()

        for uri in redirect_uris:
            if not validate_url(uri):
                # not a valid uri
                error = "URI {0} is not a valid URI".format(uri)
                return json_response({"error": error}, status=400)

        client.redirect_uri = redirect_uris

 
    client.save()

    expirey = 0 if client.expirey is None else client.expirey

    return json_response(
        {
            "client_id": client.id,
            "client_secret": client.secret,
            "expires_at": expirey,
        })

@csrf_exempt
def request_token(request):
    """ Returns request token """
    try:
        data = decode_request(request) 
    except ValueError:
        error = "Could not decode data."
        return json_response({"error": error}, status=400)

    if data == "":
        error = "Unknown Content-Type"
        return json_response({"error": error}, status=400)

    if not data and request.headers:
        data = request.headers
    
    data = dict(data) # mutableifying

    authorization = decode_authorization_header(data)

    if authorization == dict() or u"oauth_consumer_key" not in authorization:
        error = "Missing required parameter."
        return json_response({"error": error}, status=400)

    # check the client_id
    client_id = authorization[u"oauth_consumer_key"]
    client = Client.query.filter_by(id=client_id).first()

    if client == None:
        # client_id is invalid
        error = "Invalid client_id"
        return json_response({"error": error}, status=400)

   # make request token and return to client
    request_validator = GMGRequestValidator(authorization)
    rv = RequestTokenEndpoint(request_validator)
    tokens = rv.create_request_token(request, authorization)

    # store the nonce & timestamp before we return back
    nonce = authorization[u"oauth_nonce"]
    timestamp = authorization[u"oauth_timestamp"]
    timestamp = datetime.datetime.fromtimestamp(float(timestamp))

    nc = NonceTimestamp(nonce=nonce, timestamp=timestamp)
    nc.save()

    return form_response(tokens)

@require_active_login    
def authorize(request):
    """ Displays a page for user to authorize """
    if request.method == "POST":
        return authorize_finish(request)
    
    _ = pass_to_ugettext
    token = request.args.get("oauth_token", None)
    if token is None:
        # no token supplied, display a html 400 this time
        err_msg = _("Must provide an oauth_token.")
        return render_400(request, err_msg=err_msg)

    oauth_request = RequestToken.query.filter_by(token=token).first()
    if oauth_request is None:
        err_msg = _("No request token found.")
        return render_400(request, err_msg)
    
    if oauth_request.used:
        return authorize_finish(request)
    
    if oauth_request.verifier is None:
        orequest = GMGRequest(request)
        request_validator = GMGRequestValidator()
        auth_endpoint = AuthorizationEndpoint(request_validator)
        verifier = auth_endpoint.create_verifier(orequest, {})
        oauth_request.verifier = verifier["oauth_verifier"]

    oauth_request.user = request.user.id
    oauth_request.save()

    # find client & build context
    client = Client.query.filter_by(id=oauth_request.client).first()

    authorize_form = AuthorizeForm(WTFormData({
            "oauth_token": oauth_request.token,
            "oauth_verifier": oauth_request.verifier
            }))

    context = {
            "user": request.user,
            "oauth_request": oauth_request,
            "client": client,
            "authorize_form": authorize_form,
            }


    # AuthorizationEndpoint
    return render_to_response(
            request,
            "mediagoblin/api/authorize.html",
            context
            )
            

def authorize_finish(request):
    """ Finishes the authorize """
    _ = pass_to_ugettext
    token = request.form["oauth_token"]
    verifier = request.form["oauth_verifier"]
    oauth_request = RequestToken.query.filter_by(token=token, verifier=verifier)
    oauth_request = oauth_request.first()
    
    if oauth_request is None:
        # invalid token or verifier
        err_msg = _("No request token found.")
        return render_400(request, err_msg)

    oauth_request.used = True
    oauth_request.updated = datetime.datetime.now()
    oauth_request.save()

    if oauth_request.callback == "oob":
        # out of bounds
        context = {"oauth_request": oauth_request}
        return render_to_response(
                request,
                "mediagoblin/api/oob.html",
                context
                )

    # okay we need to redirect them then!
    querystring = "?oauth_token={0}&oauth_verifier={1}".format(
            oauth_request.token,
            oauth_request.verifier
            )

    return redirect(
            request,
            querystring=querystring,
            location=oauth_request.callback
            )

@csrf_exempt
def access_token(request):
    """ Provides an access token based on a valid verifier and request token """ 
    data = request.headers

    parsed_tokens = decode_authorization_header(data)    

    if parsed_tokens == dict() or "oauth_token" not in parsed_tokens:
        error = "Missing required parameter."
        return json_response({"error": error}, status=400)


    request.oauth_token = parsed_tokens["oauth_token"]
    request_validator = GMGRequestValidator(data)
    av = AccessTokenEndpoint(request_validator)
    tokens = av.create_access_token(request, {})
    return form_response(tokens)

