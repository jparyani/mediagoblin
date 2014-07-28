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

import celery
import datetime
import pytz

from mediagoblin.db.models import MediaEntry

@celery.task()
def collect_garbage():
    """
        Garbage collection to clean up media

        This will look for all critera on models to clean
        up. This is primerally written to clean up media that's
        entered a erroneous state.
    """
    cuttoff = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=1)

    garbage = MediaEntry.query.filter(MediaEntry.created < cuttoff)
    garbage = garbage.filter(MediaEntry.state == "unprocessed")

    for entry in garbage.all():
        entry.delete()
