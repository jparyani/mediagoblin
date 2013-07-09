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

from mediagoblin.tools import pluginapi

_log = logging.getLogger(__name__)


class LDAP(object):
    def __init__(self):
        self.ldap_settings = pluginapi.get_config('mediagoblin.plugins.ldap')

    def _connect(self, server):
        _log.info('Connecting to {0}.'.format(server['LDAP_SERVER_URI']))
        self.conn = ldap.initialize(server['LDAP_SERVER_URI'])

        if server['LDAP_START_TLS'] == 'true':
            _log.info('Initiating TLS')
            self.conn.start_tls_s()

    def _get_email(self, server, username):
        try:
            results = self.conn.search_s(server['LDAP_SEARCH_BASE'],
                                        ldap.SCOPE_SUBTREE, 'uid={0}'
                                        .format(username),
                                        [server['EMAIL_SEARCH_FIELD']])

            email = results[0][1][server['EMAIL_SEARCH_FIELD']][0]
        except KeyError:
            email = None

        return email

    def login(self, username, password):
        for k, v in self.ldap_settings.iteritems():
            try:
                self._connect(v)
                user_dn = v['LDAP_USER_DN_TEMPLATE'].format(username=username)
                self.conn.simple_bind_s(user_dn, password.encode('utf8'))
                email = self._get_email(v, username)
                return username, email

            except ldap.LDAPError, e:
                _log.info(e)

            finally:
                _log.info('Unbinding {0}.'.format(v['LDAP_SERVER_URI']))
                self.conn.unbind()

        return False, None
