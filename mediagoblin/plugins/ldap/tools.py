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
import ldap
import logging

from mediagoblin import mg_globals
from mediagoblin.db.models import User
from mediagoblin.tools.response import redirect

_log = logging.getLogger(__name__)


class LDAP(object):
    def __init__(self, request):
        self.ldap_settings = mg_globals.global_config['plugins']['mediagoblin.plugins.ldap']
        self.request = request

    def _connect(self, server):
        _log.info('Connecting to {0}.'.format(server['LDAP_HOST']))
        self.conn = ldap.initialize('ldap://{0}:{1}/'.format(
            server['LDAP_HOST'], server['LDAP_PORT']))

    def login(self, username, password):
        for k, v in self.ldap_settings.iteritems():
            try:
                import ipdb
                ipdb.set_trace()
                self._connect(v)
                user_dn = v['USER_DN_TEMPLATE'].format(username=username)
                self.conn.simple_bind_s(user_dn, password.encode('utf8'))
                return self._get_or_create_user(username)

            except ldap.LDAPError, e:
                _log.info(e)

        return None

    def _get_or_create_user(self, username):
        user = User.query.filter_by(
            username=username).first()

        if user:
            return user

        self.request.session['username'] = username
        redirect(
            self.request, 'mediagoblin.plugins.ldap.register')
