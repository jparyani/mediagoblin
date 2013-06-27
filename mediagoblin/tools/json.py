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

from werkzeug.wrappers import Response

def json_response(serializable, _disable_cors=False, *args, **kw):
    '''
    Serializes a json objects and returns a werkzeug Response object with the
    serialized value as the response body and Content-Type: application/json.

    :param serializable: A json-serializable object

    Any extra arguments and keyword arguments are passed to the
    Response.__init__ method.
    '''
    response = Response(json.dumps(serializable), *args, content_type='application/json', **kw)

    if not _disable_cors:
        cors_headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Requested-With'}
        for key, value in cors_headers.iteritems():
            response.headers.set(key, value)

    return response
