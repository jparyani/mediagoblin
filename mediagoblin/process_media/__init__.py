# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

import Image
from mediagoblin.db.util import ObjectId
from celery.task import task

from mediagoblin.globals import database, queue_store, public_store


THUMB_SIZE = 200, 200


@task
def process_media_initial(media_id):
    entry = database.MediaEntry.one(
        {'_id': ObjectId(media_id)})

    queued_filepath = entry['queued_media_file']
    queued_file = queue_store.get_file(queued_filepath, 'r')

    with queued_file:
        thumb = Image.open(queued_file)
        thumb.thumbnail(THUMB_SIZE, Image.ANTIALIAS)

        thumb_filepath = public_store.get_unique_filepath(
            ['media_entries',
             unicode(entry['_id']),
             'thumbnail.jpg'])

        with public_store.get_file(thumb_filepath, 'w') as thumb_file:
            thumb.save(thumb_file, "JPEG")

    # we have to re-read because unlike PIL, not everything reads
    # things in string representation :)
    queued_file = queue_store.get_file(queued_filepath, 'rb')

    with queued_file:
        main_filepath = public_store.get_unique_filepath(
            ['media_entries',
             unicode(entry['_id']),
             queued_filepath[-1]])
        
        with public_store.get_file(main_filepath, 'wb') as main_file:
            main_file.write(queued_file.read())

    queue_store.delete_file(queued_filepath)
    media_files_dict = entry.setdefault('media_files', {})
    media_files_dict['thumb'] = thumb_filepath
    media_files_dict['main'] = main_filepath
    entry['state'] = u'processed'
    entry.save()
