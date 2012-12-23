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
import base64

from werkzeug.exceptions import BadRequest, Unauthorized

from mediagoblin.plugins.api.tools import Auth

_log = logging.getLogger(__name__)


def setup_http_api_auth():
    _log.info('Setting up HTTP API Auth...')


class HTTPAuth(Auth):
    def trigger(self, request):
        if request.authorization:
            return True

        return False

    def __call__(self, request, *args, **kw):
        _log.debug('Trying to authorize the user agent via HTTP Auth')
        if not request.authorization:
            return False

        user = request.db.User.query.filter_by(
                username=unicode(request.authorization['username'])).first()

        if user.check_login(request.authorization['password']):
            request.user = user
            return True
        else:
            raise Unauthorized()

        return False



hooks = {
    'setup': setup_http_api_auth,
    'auth': HTTPAuth()}
