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

from oauthlib.oauth1 import RequestValidator, RequestTokenEndpoint

from mediagoblin.tools.translate import pass_to_ugettext
from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.tools.request import decode_request
from mediagoblin.tools.response import json_response, render_400
from mediagoblin.tools.crypto import random_string
from mediagoblin.tools.validator import validate_email, validate_url
from mediagoblin.db.models import Client, RequestToken, AccessToken

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
  
        # save it
        client = Client(
                id=client_id, 
                secret=client_secret, 
                expirey=expirey_db,
                application_type=data["application_type"],
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
    application_name=data.get("application_name", None)

    contacts = data.get("contact", None)
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

    request_uri = data.get("request_uris", None)
    if request_uri is not None:
        if type(request_uri) is not unicode:
            error = "redirect_uris must be space-seporated URLs."
            return json_respinse({"error": error}, status=400)

        request_uri = request_uri.split()

        for uri in request_uri:
            if not validate_url(uri):
                # not a valid uri
                error = "URI {0} is not a valid URI".format(uri)
                return json_response({"error": error}, status=400)

        client.request_uri = request_uri

 
    client.save()

    expirey = 0 if client.expirey is None else client.expirey

    return json_response(
        {
            "client_id": client.id,
            "client_secret": client.secret,
            "expires_at": expirey,
        })

class ValidationException(Exception):
    pass

class GMGRequestValidator(RequestValidator):

    def __init__(self, data):
        self.POST = data

    def save_request_token(self, token, request):
        """ Saves request token in db """
        client_id = self.POST[u"Authorization"][u"oauth_consumer_key"]

        request_token = RequestToken(
                token=token["oauth_token"],
                secret=token["oauth_token_secret"],
                )
        request_token.client = client_id
        request_token.save()


@csrf_exempt
def request_token(request):
    """ Returns request token """
    try:
        data = decode_request(request) 
    except ValueError:
        error = "Could not decode data."
        return json_response({"error": error}, status=400)

    if data is "":
        error = "Unknown Content-Type"
        return json_response({"error": error}, status=400)


    # Convert 'Authorization' to a dictionary
    authorization = {}
    for item in data["Authorization"].split(","):
        key, value = item.split("=", 1)
        authorization[key] = value
    data[u"Authorization"] = authorization

    # check the client_id
    client_id = data[u"Authorization"][u"oauth_consumer_key"]
    client = Client.query.filter_by(id=client_id).first()
    if client is None:
        # client_id is invalid
        error = "Invalid client_id"
        return json_response({"error": error}, status=400)

    request_validator = GMGRequestValidator(data)
    rv = RequestTokenEndpoint(request_validator)
    tokens = rv.create_request_token(request, {})

    tokenized = {}
    for t in tokens.split("&"):
        key, value = t.split("=")
        tokenized[key] = value

    # check what encoding to return them in
    return json_response(tokenized)
    
def authorize(request):
    """ Displays a page for user to authorize """
    _ = pass_to_ugettext
    token = request.args.get("oauth_token", None)
    if token is None:
        # no token supplied, display a html 400 this time
        err_msg = _("Must provide an oauth_token")
        return render_400(request, err_msg=err_msg)

    # AuthorizationEndpoint
    

@csrf_exempt
def access_token(request):
    """ Provides an access token based on a valid verifier and request token """ 
    pass
