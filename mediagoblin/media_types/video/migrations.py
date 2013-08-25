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

from mediagoblin.db.migration_tools import RegisterMigration, inspect_table

from sqlalchemy import MetaData, Column, Unicode

MIGRATIONS = {}


@RegisterMigration(1, MIGRATIONS)
def add_orig_metadata_column(db_conn):
    metadata = MetaData(bind=db_conn.bind)

    vid_data = inspect_table(metadata, "video__mediadata")

    col = Column('orig_metadata', Unicode,
                 default=None, nullable=True)
    col.create(vid_data)
    db_conn.commit()


@RegisterMigration(2, MIGRATIONS)
def webm_640_to_webm_video(db):
    metadata = MetaData(bind=db.bind)

    file_keynames = inspect_table(metadata, 'core__file_keynames')

    for row in db.execute(file_keynames.select()):
        if row.name == 'webm_640':
            db.execute(
                file_keynames.update(). \
                where(file_keynames.c.id==row.id).\
                values(name='webm_video'))

    db.commit()
