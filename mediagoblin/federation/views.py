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

        client = Client.query.filter_by(id=data["client_id"], secret=data["client_secret"]).all()

        if not client:
            return json_response({"error":"Unauthorized.", status=403)

        client.logo_url = data.get("logo_url", client.logo_url)
        client.application_name = data.get("application_name", client.application_name)
        app_name = ("application_type", client.application_name)
        if app_name in client_types:
            client.application_name = app_name
        
        client.save()

        expirey = 0 if client.expirey is None else client.expirey

        return json_response(
                {
                    "client_id":client.id,
                    "client_secret":client.secret,
                    "expires":expirey,
                })

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
        application_type=data["type"],
        logo_url=data.get("logo_url", None),
        redirect_uri=data.get("redirect_uri", None),
        application_type=data["application_type"]
    )
    client.save()

    return json_response(
        {
            "client_id":client_id,
            "client_secret":client_secret,
            "expires_at":expirey,
        })
