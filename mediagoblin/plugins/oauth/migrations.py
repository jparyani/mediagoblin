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

from sqlalchemy import MetaData, Table

from mediagoblin.db.sql.util import RegisterMigration

from mediagoblin.plugins.oauth.models import OAuthClient, OAuthToken, \
        OAuthUserClient, OAuthCode

MIGRATIONS = {}


@RegisterMigration(1, MIGRATIONS)
def remove_and_replace_token_and_code(db):
    metadata = MetaData(bind=db.bind)

    token_table = Table('oauth__tokens', metadata, autoload=True,
            autoload_with=db.bind)

    token_table.drop()

    code_table = Table('oauth__codes', metadata, autoload=True,
            autoload_with=db.bind)

    code_table.drop()

    OAuthClient.__table__.create(db.bind)
    OAuthUserClient.__table__.create(db.bind)
    OAuthToken.__table__.create(db.bind)
    OAuthCode.__table__.create(db.bind)

    db.commit()
