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

from sqlalchemy import MetaData, Column, ForeignKey

from mediagoblin.db.migration_tools import RegisterMigration, inspect_table


MIGRATIONS = {}

@RegisterMigration(1, MIGRATIONS)
def remove_gps_from_image(db):
    """
    This will remove GPS coordinates from the image model to put them
    on the new Location model.
    """
    metadata = MetaData(bind=db.bind)
    image_table = inspect_table(metadata, "image__mediadata")
    location_table = inspect_table(metadata, "core__locations")
    media_entries_table = inspect_table(metadata, "core__media_entries")

    # First do the data migration
    for row in db.execute(image_table.select()):
        fields = {
            "longitude": row.gps_longitude,
            "latitude": row.gps_latitude,
            "altitude": row.gps_altitude,
            "direction": row.gps_direction,
        }

        # Remove empty values
        for k, v in fields.items():
            if v is None:
                del fields[k]

        # No point in adding empty locations
        if not fields:
            continue

        # JSONEncoded is actually a string field just json.dumped
        # without the ORM we're responsible for that.
        fields = json.dumps(fields)

        location = db.execute(location_table.insert().values(position=fields))

        # now store the new location model on Image
        db.execute(media_entries_table.update().values(
            location=location.inserted_primary_key[0]
        ).where(media_entries_table.c.id==row.media_entry))

    db.commit()

    # All that data has been migrated across lets remove the fields
    image_table.columns["gps_longitude"].drop()
    image_table.columns["gps_latitude"].drop()
    image_table.columns["gps_altitude"].drop()
    image_table.columns["gps_direction"].drop()

    db.commit()
