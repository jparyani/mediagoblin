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
import urllib
import urllib2

from celery import registry, task

from mediagoblin import mg_globals as mgg
from mediagoblin.db.models import MediaEntry
from . import mark_entry_failed, BaseProcessingFail, ProcessingState
from mediagoblin.tools.processing import json_processing_callback

_log = logging.getLogger(__name__)
logging.basicConfig()
_log.setLevel(logging.DEBUG)


@task.task(default_retry_delay=2 * 60)
def handle_push_urls(feed_url):
    """Subtask, notifying the PuSH servers of new content

    Retry 3 times every 2 minutes if run in separate process before failing."""
    if not mgg.app_config["push_urls"]:
        return # Nothing to do
    _log.debug('Notifying Push servers for feed {0}'.format(feed_url))
    hubparameters = {
        'hub.mode': 'publish',
        'hub.url': feed_url}
    hubdata = urllib.urlencode(hubparameters)
    hubheaders = {
        "Content-type": "application/x-www-form-urlencoded",
        "Connection": "close"}
    for huburl in mgg.app_config["push_urls"]:
        hubrequest = urllib2.Request(huburl, hubdata, hubheaders)
        try:
            hubresponse = urllib2.urlopen(hubrequest)
        except (urllib2.HTTPError, urllib2.URLError) as exc:
            # We retry by default 3 times before failing
            _log.info("PuSH url %r gave error %r", huburl, exc)
            try:
                return handle_push_urls.retry(exc=exc, throw=False)
            except Exception as e:
                # All retries failed, Failure is no tragedy here, probably.
                _log.warn('Failed to notify PuSH server for feed {0}. '
                          'Giving up.'.format(feed_url))
                return False

################################
# Media processing initial steps
################################

class ProcessMedia(task.Task):
    """
    Pass this entry off for processing.
    """
    def run(self, media_id, feed_url):
        """
        Pass the media entry off to the appropriate processing function
        (for now just process_image...)

        :param feed_url: The feed URL that the PuSH server needs to be
            updated for.
        """
        entry = MediaEntry.query.get(media_id)

        # Try to process, and handle expected errors.
        try:
            entry.state = u'processing'
            entry.save()

            _log.debug('Processing {0}'.format(entry))

            proc_state = ProcessingState(entry)
            with mgg.workbench_manager.create() as workbench:
                proc_state.set_workbench(workbench)
                # run the processing code
                entry.media_manager.processor(proc_state)

            # We set the state to processed and save the entry here so there's
            # no need to save at the end of the processing stage, probably ;)
            entry.state = u'processed'
            entry.save()

            # Notify the PuSH servers as async task
            if mgg.app_config["push_urls"] and feed_url:
                handle_push_urls.subtask().delay(feed_url)

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

# Register the task
process_media = registry.tasks[ProcessMedia.name]

