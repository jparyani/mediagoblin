# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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
import tempfile

from celery.task import Task
from celery import registry

from mediagoblin.db.util import ObjectId
from mediagoblin import mg_globals as mgg

from mediagoblin.util import lazy_pass_to_ugettext as _

import gobject

import gst
import arista

from arista.transcoder import TranscoderOptions

THUMB_SIZE = 180, 180
MEDIUM_SIZE = 640, 640
ARISTA_DEVICE_KEY = 'web'


loop = None


def process_video(entry):
    """
    Code to process a video
    """
    info = {}
    workbench = mgg.workbench_manager.create_workbench()

    queued_filepath = entry['queued_media_file']
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    arista.init()

    devices = arista.presets.get()
    device = devices[ARISTA_DEVICE_KEY]

    queue = arista.queue.TranscodeQueue()
    
    info['tmp_file'] = tmp_file = tempfile.NamedTemporaryFile()

    info['medium_filepath'] = medium_filepath = create_pub_filepath(entry, 'video.webm')

    output = tmp_file.name

    uri = 'file://' + queued_filename

    preset = device.presets[device.default]

    opts = TranscoderOptions(uri, preset, output)

    queue.append(opts)

    info['entry'] = entry

    queue.connect("entry-start", entry_start, info)
#    queue.connect("entry-pass-setup", entry_pass_setup, options)
    queue.connect("entry-error", entry_error, info)
    queue.connect("entry-complete", entry_complete, info)

    info['loop'] = loop = gobject.MainLoop()

    loop.run()

    # we have to re-read because unlike PIL, not everything reads
    # things in string representation :)
    queued_file = file(queued_filename, 'rb')

    with queued_file:
        original_filepath = create_pub_filepath(entry, queued_filepath[-1])

        with mgg.public_store.get_file(original_filepath, 'wb') as original_file:
            original_file.write(queued_file.read())

    mgg.queue_store.delete_file(queued_filepath)
    entry['queued_media_file'] = []
    media_files_dict = entry.setdefault('media_files', {})
    media_files_dict['original'] = original_filepath

    # clean up workbench
    workbench.destroy_self()
    

def create_pub_filepath(entry, filename):
    return mgg.public_store.get_unique_filepath(
            ['media_entries',
             unicode(entry['_id']),
             filename])


class BaseProcessingFail(Exception):
    """
    Base exception that all other processing failure messages should
    subclass from.
  
    You shouldn't call this itself; instead you should subclass it
    and provid the exception_path and general_message applicable to
    this error.
    """
    general_message = u''
  
    @property
    def exception_path(self):
        return u"%s:%s" % (
            self.__class__.__module__, self.__class__.__name__)

    def __init__(self, **metadata):
        self.metadata = metadata or {}
  
  
class BadMediaFail(BaseProcessingFail):
    """
    Error that should be raised when an inappropriate file was given
    for the media type specified.
    """
    general_message = _(u'Invalid file given for media type.')


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
        entry = mgg.database.MediaEntry.one(
            {'_id': ObjectId(media_id)})

        # Try to process, and handle expected errors.
        try:
            process_video(entry)
        except BaseProcessingFail, exc:
            mark_entry_failed(entry[u'_id'], exc)
            return

        entry['state'] = u'processed'
        entry.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        If the processing failed we should mark that in the database.

        Assuming that the exception raised is a subclass of BaseProcessingFail,
        we can use that to get more information about the failure and store that
        for conveying information to users about the failure, etc.
        """
        entry_id = args[0]
        mark_entry_failed(entry_id, exc)


process_media = registry.tasks[ProcessMedia.name]


def mark_entry_failed(entry_id, exc):
    """
    Mark a media entry as having failed in its conversion.

    Uses the exception that was raised to mark more information.  If the
    exception is a derivative of BaseProcessingFail then we can store extra
    information that can be useful for users telling them why their media failed
    to process.

    Args:
     - entry_id: The id of the media entry

    """
    # Was this a BaseProcessingFail?  In other words, was this a
    # type of error that we know how to handle?
    if isinstance(exc, BaseProcessingFail):
        # Looks like yes, so record information about that failure and any
        # metadata the user might have supplied.
        mgg.database['media_entries'].update(
            {'_id': entry_id},
            {'$set': {u'state': u'failed',
                      u'fail_error': exc.exception_path,
                      u'fail_metadata': exc.metadata}})
    else:
        # Looks like no, so just mark it as failed and don't record a
        # failure_error (we'll assume it wasn't handled) and don't record
        # metadata (in fact overwrite it if somehow it had previous info
        # here)
        mgg.database['media_entries'].update(
            {'_id': entry_id},
            {'$set': {u'state': u'failed',
                      u'fail_error': None,
                      u'fail_metadata': {}}})


def entry_start(queue, entry, options):
    print(queue, entry, options)

def entry_complete(queue, entry, info):
    entry.transcoder.stop()
    gobject.idle_add(info['loop'].quit)

    with info['tmp_file'] as tmp_file:
        mgg.public_store.get_file(info['medium_filepath'], 'wb').write(
            tmp_file.read())
        info['entry']['media_files']['medium'] = info['medium_filepath']

    print('\n=== DONE! ===\n')

    print(queue, entry, info)

def entry_error(queue, entry, options):
    print(queue, entry, options)

def signal_handler(signum, frame):
    """
        Handle Ctr-C gracefully and shut down the transcoder.
    """
    global interrupted
    print
    print _("Interrupt caught. Cleaning up... (Ctrl-C to force exit)")
    interrupted = True
    signal.signal(signal.SIGINT, signal.SIG_DFL)

def check_interrupted():
    """
        Check whether we have been interrupted by Ctrl-C and stop the
        transcoder.
    """
    if interrupted:
        try:
            source = transcoder.pipe.get_by_name("source")
            source.send_event(gst.event_new_eos())
        except:
            # Something pretty bad happened... just exit!
            gobject.idle_add(loop.quit)
            
        return False
    return True
