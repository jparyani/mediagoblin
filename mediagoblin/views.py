# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

from webob import Response
from mediagoblin.db.util import DESCENDING

def root_view(request):
    media_entries = request.db.MediaEntry.find(
        {u'state': u'processed'}).sort('created', DESCENDING)
    
    template = request.template_env.get_template(
        'mediagoblin/root.html')
    return Response(
        template.render(
            {'request': request,
             'media_entries': media_entries}))
