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

import json

from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.tools.response import json_response 
from mediagoblin.tools.crypto import random_string
from mediagoblin.tools.validator import validate_email, validate_url
from mediagoblin.db.models import Client

# possible client types
client_types = ["web", "native"] # currently what pump supports

@csrf_exempt
def client_register(request):
    """ Endpoint for client registration """
    data = request.get_data()
    if request.content_type == "application/json":
        try:
            data = json.loads(data)
        except ValueError:
            return json_response({"error":"Could not decode JSON"})
    elif request.content_type == "" or request.content_type == "application/x-www-form-urlencoded":
        data = request.form
    else:
        return json_response({"error":"Unknown Content-Type"}, status=400)

    if "type" not in data:
        return json_response({"error":"No registration type provided"}, status=400)
    if "application_type" not in data or data["application_type"] not in client_types:
        return json_response({"error":"Unknown application_type."}, status=400)
    
    client_type = data["type"]

    if client_type == "client_update":
        # updating a client
        if "client_id" not in data:
            return json_response({"error":"client_id is required to update."}, status=400)
        elif "client_secret" not in data:
            return json_response({"error":"client_secret is required to update."}, status=400)

        client = Client.query.filter_by(id=data["client_id"], secret=data["client_secret"]).first()

        if client is None:
            return json_response({"error":"Unauthorized."}, status=403)

        client.application_name = data.get("application_name", client.application_name)
        client.application_type = data.get("application_type", client.application_type)
        app_name = ("application_type", client.application_name)
        if app_name in client_types:
            client.application_name = app_name

    elif client_type == "client_associate":
        # registering
        if "client_id" in data:
            return json_response({"error":"Only set client_id for update."}, status=400)
        elif "access_token" in data:
            return json_response({"error":"access_token not needed for registration."}, status=400)
        elif "client_secret" in data:
            return json_response({"error":"Only set client_secret for update."}, status=400)

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
        return json_response({"error":"Invalid registration type"}, status=400)

    logo_url = data.get("logo_url", client.logo_url)
    if logo_url is not None and not validate_url(logo_url):
        return json_response({"error":"Logo URL {0} is not a valid URL".format(logo_url)}, status=400)
    else:
        client.logo_url = logo_url
    application_name=data.get("application_name", None)

    contacts = data.get("contact", None)
    if contacts is not None:
        if type(contacts) is not unicode:
            return json_response({"error":"contacts must be a string of space-separated email addresses."}, status=400)

        contacts = contacts.split()
        for contact in contacts:
            if not validate_email(contact):
                # not a valid email
                return json_response({"error":"Email {0} is not a valid email".format(contact)}, status=400)
     
        
        client.contacts = contacts

    request_uri = data.get("request_uris", None)
    if request_uri is not None:
        if type(request_uri) is not unicode:
            return json_respinse({"error":"redirect_uris must be space-separated URLs."}, status=400)

        request_uri = request_uri.split()

        for uri in request_uri:
            if not validate_url(uri):
                # not a valid uri
                return json_response({"error":"URI {0} is not a valid URI".format(uri)}, status=400)

        client.request_uri = request_uri

 
    client.save()

    expirey = 0 if client.expirey is None else client.expirey

    return json_response(
        {
            "client_id":client.id,
            "client_secret":client.secret,
            "expires_at":expirey,
        })
