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
from functools import wraps

from mediagoblin.db.models import User
from mediagoblin.decorators import require_active_login
from mediagoblin.tools.response import json_response

def user_has_privilege(privilege_name):
    """
    Requires that a user have a particular privilege in order to access a page.
    In order to require that a user have multiple privileges, use this
    decorator twice on the same view. This decorator also makes sure that the
    user is not banned, or else it redirects them to the "You are Banned" page.

        :param privilege_name       A unicode object that is that represents
                                        the privilege object. This object is
                                        the name of the privilege, as assigned
                                        in the Privilege.privilege_name column
    """

    def user_has_privilege_decorator(controller):
        @wraps(controller)
        @require_active_login
        def wrapper(request, *args, **kwargs):
            if not request.user.has_privilege(privilege_name):
                error = "User '{0}' needs '{1}' privilege".format(
                    request.user.username,
                    privilege_name
                )
                return json_response({"error": error}, status=403)

            return controller(request, *args, **kwargs)

        return wrapper
    return user_has_privilege_decorator
