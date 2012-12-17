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

import urllib
import urllib2
import logging

from mediagoblin import mg_globals

_log = logging.getLogger(__name__)


def handle_push_urls(request):
    if mg_globals.app_config["push_urls"]:
        feed_url = request.urlgen(
                           'mediagoblin.user_pages.atom_feed',
                           qualified=True,
                           user=request.user.username)
        hubparameters = {
            'hub.mode': 'publish',
            'hub.url': feed_url}
        hubdata = urllib.urlencode(hubparameters)
        hubheaders = {
            "Content-type": "application/x-www-form-urlencoded",
            "Connection": "close"}
        for huburl in mg_globals.app_config["push_urls"]:
            hubrequest = urllib2.Request(huburl, hubdata, hubheaders)
            try:
                hubresponse = urllib2.urlopen(hubrequest)
            except urllib2.HTTPError as exc:
                # This is not a big issue, the item will be fetched
                # by the PuSH server next time we hit it
                _log.warning(
                    "push url %r gave error %r", huburl, exc.code)
            except urllib2.URLError as exc:
                _log.warning(
                    "push url %r is unreachable %r", huburl, exc.reason)
