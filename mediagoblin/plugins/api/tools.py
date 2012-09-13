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

from functools import wraps
from webob import exc

from mediagoblin.tools.pluginapi import PluginManager

_log = logging.getLogger(__name__)


def api_auth(controller):
    @wraps(controller)
    def wrapper(request, *args, **kw):
        auth_candidates = []

        for auth in PluginManager().get_hook_callables('auth'):
            _log.debug('Plugin auth: {0}'.format(auth))
            if auth.trigger(request):
                auth_candidates.append(auth)

        # If we can't find any authentication methods, we should not let them
        # pass.
        if not auth_candidates:
            return exc.HTTPForbidden()

        # For now, just select the first one in the list
        auth = auth_candidates[0]

        _log.debug('Using {0} to authorize request {1}'.format(
            auth, request.url))

        if not auth(request, *args, **kw):
            return exc.HTTPForbidden()

        return controller(request, *args, **kw)

    return wrapper
