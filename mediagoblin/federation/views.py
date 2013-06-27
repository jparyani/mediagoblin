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

from mediagoblin.tools.json import json_response 

# possible client types
client_types = ["web", "native"] # currently what pump supports

def client_register(request):
    """ Endpoint for client registration """
    if request.method == "POST":
        # new client registration

        return json_response({"dir":dir(request)}) 

        # check they haven't given us client_id or client_type, they're only used for updating
        pass 

    elif request.method == "PUT":
        # updating client
        pass
