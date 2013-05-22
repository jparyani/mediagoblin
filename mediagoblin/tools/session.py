# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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

import itsdangerous
import logging

import crypto

_log = logging.getLogger(__name__)

MAX_AGE = 30 * 24 * 60 * 60

class Session(dict):
    def __init__(self, *args, **kwargs):
        self.send_new_cookie = False
        dict.__init__(self, *args, **kwargs)

    def save(self):
        self.send_new_cookie = True

    def is_updated(self):
        return self.send_new_cookie

    def delete(self):
        self.clear()
        self.save()


class SessionManager(object):
    def __init__(self, cookie_name='MGSession', namespace=None):
        if namespace is None:
            namespace = cookie_name
        self.signer = crypto.get_timed_signer_url(namespace)
        self.cookie_name = cookie_name

    def load_session_from_cookie(self, request):
        cookie = request.cookies.get(self.cookie_name)
        if not cookie:
            return Session()
        ### FIXME: Future cookie-blacklisting code
        # m = BadCookie.query.filter_by(cookie = cookie)
        # if m:
        #     _log.warn("Bad cookie received: %s", m.reason)
        #     raise BadRequest()
        try:
            return Session(self.signer.loads(cookie))
        except itsdangerous.BadData:
            return Session()

    def save_session_to_cookie(self, session, request, response):
        if not session.is_updated():
            return
        elif not session:
            response.delete_cookie(self.cookie_name)
        else:
            if session.get('stay_logged_in', False):
                max_age = MAX_AGE
            else:
                max_age = None

            response.set_cookie(self.cookie_name, self.signer.dumps(session),
                max_age=max_age, httponly=True)
