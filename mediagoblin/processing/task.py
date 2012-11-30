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

import logging

from celery.task import Task

from mediagoblin import mg_globals as mgg
from mediagoblin.db.models import MediaEntry
from mediagoblin.processing import mark_entry_failed, BaseProcessingFail
from mediagoblin.tools.processing import json_processing_callback

_log = logging.getLogger(__name__)
logging.basicConfig()
_log.setLevel(logging.DEBUG)


################################
# Media processing initial steps
################################

class ProcessMedia(Task):
    """
    Pass this entry off for processing.
    """
    def run(self, media_id):
        """
        Pass the media entry off to the appropriate processing function
        (for now just process_image...)
        """
        entry = MediaEntry.query.get(media_id)

        # Try to process, and handle expected errors.
        try:
            entry.state = u'processing'
            entry.save()

            _log.debug('Processing {0}'.format(entry))

            # run the processing code
            entry.media_manager['processor'](entry)

            # We set the state to processed and save the entry here so there's
            # no need to save at the end of the processing stage, probably ;)
            entry.state = u'processed'
            entry.save()

            json_processing_callback(entry)
        except BaseProcessingFail as exc:
            mark_entry_failed(entry.id, exc)
            json_processing_callback(entry)
            return

        except ImportError as exc:
            _log.error(
                'Entry {0} failed to process due to an import error: {1}'\
                    .format(
                    entry.title,
                    exc))

            mark_entry_failed(entry.id, exc)
            json_processing_callback(entry)

        except Exception as exc:
            _log.error('An unhandled exception was raised while'
                    + ' processing {0}'.format(
                        entry))

            mark_entry_failed(entry.id, exc)
            json_processing_callback(entry)
            raise

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        If the processing failed we should mark that in the database.

        Assuming that the exception raised is a subclass of
        BaseProcessingFail, we can use that to get more information
        about the failure and store that for conveying information to
        users about the failure, etc.
        """
        entry_id = args[0]
        mark_entry_failed(entry_id, exc)

        entry = mgg.database.MediaEntry.query.filter_by(id=entry_id).first()
        json_processing_callback(entry)
