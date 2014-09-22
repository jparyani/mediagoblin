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
import base64
import time

import six

from openid.association import Association as OIDAssociation
from openid.store.interface import OpenIDStore
from openid.store import nonce

from mediagoblin.plugins.openid.models import Association, Nonce


class SQLAlchemyOpenIDStore(OpenIDStore):
    def __init__(self):
        self.max_nonce_age = 6 * 60 * 60

    def storeAssociation(self, server_url, association):
        assoc = Association.query.filter_by(
            server_url=server_url, handle=association.handle
        ).first()

        if not assoc:
            assoc = Association()
            assoc.server_url = six.text_type(server_url)
            assoc.handle = association.handle

        # django uses base64 encoding, python-openid uses a blob field for
        # secret
        assoc.secret = six.text_type(base64.encodestring(association.secret))
        assoc.issued = association.issued
        assoc.lifetime = association.lifetime
        assoc.assoc_type = association.assoc_type
        assoc.save()

    def getAssociation(self, server_url, handle=None):
        assocs = []
        if handle is not None:
            assocs = Association.query.filter_by(
                server_url=server_url, handle=handle
            )
        else:
            assocs = Association.query.filter_by(
                server_url=server_url
            )

        if assocs.count() == 0:
            return None
        else:
            associations = []
            for assoc in assocs:
                association = OIDAssociation(
                    assoc.handle, base64.decodestring(assoc.secret),
                    assoc.issued, assoc.lifetime, assoc.assoc_type
                )
                if association.getExpiresIn() == 0:
                    assoc.delete()
                else:
                    associations.append((association.issued, association))

            if not associations:
                return None
            associations.sort()
            return associations[-1][1]

    def removeAssociation(self, server_url, handle):
        assocs = Association.query.filter_by(
            server_url=server_url, handle=handle
        ).first()

        assoc_exists = True if assocs else False
        for assoc in assocs:
            assoc.delete()
        return assoc_exists

    def useNonce(self, server_url, timestamp, salt):
        if abs(timestamp - time.time()) > nonce.SKEW:
            return False

        ononce = Nonce.query.filter_by(
            server_url=server_url,
            timestamp=timestamp,
            salt=salt
        ).first()

        if ononce:
            return False
        else:
            ononce = Nonce()
            ononce.server_url = server_url
            ononce.timestamp = timestamp
            ononce.salt = salt
            ononce.save()
            return True

    def cleanupNonces(self, _now=None):
        if _now is None:
            _now = int(time.time())
        expired = Nonce.query.filter(
            Nonce.timestamp < (_now - nonce.SKEW)
        )
        count = expired.count()
        for each in expired:
            each.delete()
        return count

    def cleanupAssociations(self):
        now = int(time.time())
        assoc = Association.query.all()
        count = 0
        for each in assoc:
            if (each.lifetime + each.issued) <= now:
                each.delete()
                count = count + 1
        return count
