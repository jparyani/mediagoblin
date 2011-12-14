# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

import re
import mediagoblin.mg_globals as mg_globals

from mediagoblin.tools.response import render_to_response

LRDD_TEMPLATE = '{protocol}://{host}/api/webfinger/xrd?uri={{uri}}'

def host_meta(request):
    '''
    Webfinger host-meta
    '''
    return render_to_response(
        request,
        'mediagoblin/webfinger/host-meta.xml',
        {'request': request,
         'lrdd_template': LRDD_TEMPLATE.format(
                protocol='http',
                host=request.host)})

def xrd(request):
    ''' 
    Find user data based on a webfinger URI
    '''
    return render_to_response(
        request,
        'mediagoblin/webfinger/xrd.xml',
        {'request': request,
         'username': re.search(
                r'^acct:([^@]*)',
                request.GET.get('uri')).group(1)})
