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

from werkzeug import Response


def static_demo(request):
    return Response(json.dumps({
        # this does not exist, but we'll pretend it does ;)
        'mgoblin_bunny_pic': request.staticdirect(
            'images/bunny_pic.png'),
        'plugin_bunny_css': request.staticdirect(
            'css/bunnify.css', 'staticstuff')}))
