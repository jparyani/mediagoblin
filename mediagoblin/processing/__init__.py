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

# Use an ordered dict if we can.  If not, we'll just use a normal dict
# later.
try:
    from collections import OrderedDict
except:
    OrderedDict = None

import logging
import os

from mediagoblin import mg_globals as mgg
from mediagoblin.db.util import atomic_update
from mediagoblin.db.models import MediaEntry
from mediagoblin.tools.pluginapi import hook_handle
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

_log = logging.getLogger(__name__)


class ProgressCallback(object):
    def __init__(self, entry):
        self.entry = entry

    def __call__(self, progress):
        if progress:
            self.entry.transcoding_progress = progress
            self.entry.save()


def create_pub_filepath(entry, filename):
    return mgg.public_store.get_unique_filepath(
            ['media_entries',
             unicode(entry.id),
             filename])


class FilenameBuilder(object):
    """Easily slice and dice filenames.

    Initialize this class with an original file path, then use the fill()
    method to create new filenames based on the original.

    """
    MAX_FILENAME_LENGTH = 255  # VFAT's maximum filename length

    def __init__(self, path):
        """Initialize a builder from an original file path."""
        self.dirpath, self.basename = os.path.split(path)
        self.basename, self.ext = os.path.splitext(self.basename)
        self.ext = self.ext.lower()

    def fill(self, fmtstr):
        """Build a new filename based on the original.

        The fmtstr argument can include the following:
        {basename} -- the original basename, with the extension removed
        {ext} -- the original extension, always lowercase

        If necessary, {basename} will be truncated so the filename does not
        exceed this class' MAX_FILENAME_LENGTH in length.

        """
        basename_len = (self.MAX_FILENAME_LENGTH -
                        len(fmtstr.format(basename='', ext=self.ext)))
        return fmtstr.format(basename=self.basename[:basename_len],
                             ext=self.ext)



class MediaProcessor(object):
    """A particular processor for this media type.

    While the ProcessingManager handles all types of MediaProcessing
    possible for a particular media type, a MediaProcessor can be
    thought of as a *particular* processing action for a media type.
    For example, you may have separate MediaProcessors for:

    - initial_processing: the intial processing of a media
    - gen_thumb: generate a thumbnail
    - resize: resize an image
    - transcode: transcode a video

    ... etc.

    Some information on producing a new MediaProcessor for your media type:

    - You *must* supply a name attribute.  This must be a class level
      attribute, and a string.  This will be used to determine the
      subcommand of your process
    - It's recommended that you supply a class level description
      attribute.
    - Supply a media_is_eligible classmethod.  This will be used to
      determine whether or not a media entry is eligible to use this
      processor type.  See the method documentation for details.
    - To give "./bin/gmg reprocess run" abilities to this media type,
      supply both gnerate_parser and parser_to_request classmethods.
    - The process method will be what actually processes your media.
    """
    # You MUST override this in the child MediaProcessor!
    name = None

    # Optional, but will be used in various places to describe the
    # action this MediaProcessor provides
    description = None

    def __init__(self, manager, entry):
        self.manager = manager
        self.entry = entry
        self.entry_orig_state = entry.state

        # Should be initialized at time of processing, at least
        self.workbench = None

    def __enter__(self):
        self.workbench = mgg.workbench_manager.create()
        return self

    def __exit__(self, *args):
        self.workbench.destroy()
        self.workbench = None

    # @with_workbench
    def process(self, **kwargs):
        """
        Actually process this media entry.
        """
        raise NotImplementedError

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
        raise NotImplementedError

    ###############################
    # Command line interface things
    ###############################

    @classmethod
    def generate_parser(cls):
        raise NotImplementedError

    @classmethod
    def args_to_request(cls, args):
        raise NotImplementedError

    ##########################################
    # THE FUTURE: web interface things here :)
    ##########################################

    #####################
    # Some common "steps"
    #####################

    def delete_queue_file(self):
        # Remove queued media file from storage and database.
        # queued_filepath is in the task_id directory which should
        # be removed too, but fail if the directory is not empty to be on
        # the super-safe side.
        queued_filepath = self.entry.queued_media_file
        if queued_filepath:
            mgg.queue_store.delete_file(queued_filepath)      # rm file
            mgg.queue_store.delete_dir(queued_filepath[:-1])  # rm dir
            self.entry.queued_media_file = []


class ProcessingKeyError(Exception): pass
class ProcessorDoesNotExist(ProcessingKeyError): pass
class ProcessorNotEligible(ProcessingKeyError): pass
class ProcessingManagerDoesNotExist(ProcessingKeyError): pass



class ProcessingManager(object):
    """Manages all the processing actions available for a media type

    Specific processing actions, MediaProcessor subclasses, are added
    to the ProcessingManager.
    """
    def __init__(self):
        # Dict of all MediaProcessors of this media type
        if OrderedDict is not None:
            self.processors = OrderedDict()
        else:
            self.processors = {}

    def add_processor(self, processor):
        """
        Add a processor class to this media type
        """
        name = processor.name
        if name is None:
            raise AttributeError("Processor class's .name attribute not set")

        self.processors[name] = processor

    def list_eligible_processors(self, entry):
        """
        List all processors that this media entry is eligible to be processed
        for.
        """
        return [
            processor
            for processor in self.processors.values()
            if processor.media_is_eligible(entry=entry)]

    def list_all_processors_by_state(self, state):
        """
        List all processors that this media state is eligible to be processed
        for.
        """
        return [
            processor
            for processor in self.processors.values()
            if processor.media_is_eligible(state=state)]


    def list_all_processors(self):
        return self.processors.values()

    def gen_process_request_via_cli(self, subparser):
        # Got to figure out what actually goes here before I can write this properly
        pass

    def get_processor(self, key, entry=None):
        """
        Get the processor with this key.

        If entry supplied, make sure this entry is actually compatible;
        otherwise raise error.
        """
        try:
            processor = self.processors[key]
        except KeyError:
            import pdb
            pdb.set_trace()
            raise ProcessorDoesNotExist(
                "'%s' processor does not exist for this media type" % key)

        if entry and not processor.media_is_eligible(entry):
            raise ProcessorNotEligible(
                "This entry is not eligible for processor with name '%s'" % key)

        return processor


def request_from_args(args, which_args):
    """
    Generate a request from the values of some argparse parsed args
    """
    request = {}
    for arg in which_args:
        request[arg] = getattr(args, arg)

    return request


class MediaEntryNotFound(Exception): pass


def get_processing_manager_for_type(media_type):
    """
    Get the appropriate media manager for this type
    """
    manager_class = hook_handle(('reprocess_manager', media_type))
    if not manager_class:
        raise ProcessingManagerDoesNotExist(
            "A processing manager does not exist for {0}".format(media_type))
    manager = manager_class()

    return manager


def get_entry_and_processing_manager(media_id):
    """
    Get a MediaEntry, its media type, and its manager all in one go.

    Returns a tuple of: `(entry, media_type, media_manager)`
    """
    entry = MediaEntry.query.filter_by(id=media_id).first()
    if entry is None:
        raise MediaEntryNotFound("Can't find media with id '%s'" % media_id)

    manager = get_processing_manager_for_type(entry.media_type)

    return entry, manager


def mark_entry_failed(entry_id, exc):
    """
    Mark a media entry as having failed in its conversion.

    Uses the exception that was raised to mark more information.  If
    the exception is a derivative of BaseProcessingFail then we can
    store extra information that can be useful for users telling them
    why their media failed to process.

    Args:
     - entry_id: The id of the media entry

    """
    # Was this a BaseProcessingFail?  In other words, was this a
    # type of error that we know how to handle?
    if isinstance(exc, BaseProcessingFail):
        # Looks like yes, so record information about that failure and any
        # metadata the user might have supplied.
        atomic_update(mgg.database.MediaEntry,
            {'id': entry_id},
            {u'state': u'failed',
             u'fail_error': unicode(exc.exception_path),
             u'fail_metadata': exc.metadata})
    else:
        _log.warn("No idea what happened here, but it failed: %r", exc)
        # Looks like no, so just mark it as failed and don't record a
        # failure_error (we'll assume it wasn't handled) and don't record
        # metadata (in fact overwrite it if somehow it had previous info
        # here)
        atomic_update(mgg.database.MediaEntry,
            {'id': entry_id},
            {u'state': u'failed',
             u'fail_error': None,
             u'fail_metadata': {}})


def get_process_filename(entry, workbench, acceptable_files):
    """
    Try and get the queued file if available, otherwise return the first file
    in the acceptable_files that we have.

    If no acceptable_files, raise ProcessFileNotFound
    """
    if entry.queued_media_file:
        filepath = entry.queued_media_file
        storage = mgg.queue_store
    else:
        for keyname in acceptable_files:
            if entry.media_files.get(keyname):
                filepath = entry.media_files[keyname]
                storage = mgg.public_store
                break

    if not filepath:
        raise ProcessFileNotFound()

    filename = workbench.localized_file(
        storage, filepath,
        'source')

    if not os.path.exists(filename):
        raise ProcessFileNotFound()

    return filename


def store_public(entry, keyname, local_file, target_name=None,
                 delete_if_exists=True):
    if target_name is None:
        target_name = os.path.basename(local_file)
    target_filepath = create_pub_filepath(entry, target_name)

    if keyname in entry.media_files:
        _log.warn("store_public: keyname %r already used for file %r, "
                  "replacing with %r", keyname,
                  entry.media_files[keyname], target_filepath)
        if delete_if_exists:
            mgg.public_store.delete_file(entry.media_files[keyname])

    try:
        mgg.public_store.copy_local_to_storage(local_file, target_filepath)
    except:
        raise PublicStoreFail(keyname=keyname)

    # raise an error if the file failed to copy
    if not mgg.public_store.file_exists(target_filepath):
        raise PublicStoreFail(keyname=keyname)

    entry.media_files[keyname] = target_filepath


def copy_original(entry, orig_filename, target_name, keyname=u"original"):
    store_public(entry, keyname, orig_filename, target_name)


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


class PublicStoreFail(BaseProcessingFail):
    """
    Error that should be raised when copying to public store fails
    """
    general_message = _('Copying to public storage failed.')


class ProcessFileNotFound(BaseProcessingFail):
    """
    Error that should be raised when an acceptable file for processing
    is not found.
    """
    general_message = _(u'An acceptable processing file was not found')
