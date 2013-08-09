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
import argparse
import os

from mediagoblin import mg_globals
from mediagoblin.db.models import MediaEntry
from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.tools.pluginapi import hook_handle


def reprocess_parser_setup(subparser):
    subparsers = subparser.add_subparsers(dest="reprocess_subcommand")

    ###################
    # available command
    ###################
    available_parser = subparsers.add_parser(
        "available",
        help="Find out what actions are available for this media")
    
    available_parser.add_argument(
        "id_or_type",
        help="Media id or media type to check")

    
    ############################################
    # run command (TODO: and bulk_run command??)
    ############################################
    
    run_parser = subparsers.add_parser(
        "run",
        help="Run a reprocessing on one or more media")

    run_parser.add_argument(
        '--state', '-s',
        help="Reprocess media entries in this state"
             " such as 'failed' or 'processed'")
    run_parser.add_argument(
        '--type', '-t',
        help="The type of media to be reprocessed such as 'video' or 'image'")
    run_parser.add_argument(
        '--thumbnails',
        action="store_true",
        help="Regenerate thumbnails for all processed media")
    run_parser.add_argument(
        '--celery',
        action='store_true',
        help="Don't process eagerly, pass off to celery")

    run_parser.add_argument(
        'media_id',
        help="The media_entry id(s) you wish to reprocess.")

    run_parser.add_argument(
        'reprocess_command',
        help="The reprocess command you intend to run")

    run_parser.add_argument(
        'reprocess_args',
        nargs=argparse.REMAINDER,
        help="rest of arguments to the reprocessing tool")


    ###############
    # help command?
    ###############



def _set_media_type(args):
    """
    This will verify that all media id's are of the same media_type. If the
    --type flag is set, it will be replaced by the given media id's type.

    If they are trying to process different media types, an Exception will be
    raised.
    """
    if args[0].media_id:
        if len(args[0].media_id) == 1:
            args[0].type = MediaEntry.query.filter_by(id=args[0].media_id[0])\
                .first().media_type.split('.')[-1]

        elif len(args[0].media_id) > 1:
            media_types = []

            for id in args[0].media_id:
                media_types.append(MediaEntry.query.filter_by(id=id).first()
                                   .media_type.split('.')[-1])
            for type in media_types:
                if media_types[0] != type:
                    raise Exception((u'You cannot reprocess different'
                                     ' media_types at the same time.'))

            args[0].type = media_types[0]


def _reprocess_all(args):
    """
    This handles reprocessing if no media_id's are given.
    """
    if not args[0].type:
        # If no media type is given, we can either regenerate all thumbnails,
        # or try to reprocess all failed media

        if args[0].thumbnails:
            if args[0].available:
                print _('Available options for regenerating all processed'
                        ' media thumbnails: \n'
                        '\t --size: max_width max_height'
                        ' (defaults to config specs)')
            else:
                #TODO regenerate all thumbnails
                pass

        # Reprocess all failed media
        elif args[0].state == 'failed':
            if args[0].available:
                print _('\n Available reprocess actions for all failed'
                        ' media_entries: \n \t --initial_processing')
            else:
                #TODO reprocess all failed entries
                pass

        # If here, they didn't set the --type flag and were trying to do
        # something other the generating thumbnails or initial_processing
        else:
            raise Exception(_('You must set --type when trying to reprocess'
                              ' all media_entries, unless you set --state'
                              ' to "failed".'))

    else:
        _run_reprocessing(args)


def _run_reprocessing(args):
    # Are they just asking for the available reprocessing options for the given
    # media?
    if args[0].available:
        if args[0].state == 'failed':
            print _('\n Available reprocess actions for all failed'
                    ' media_entries: \n \t --initial_processing')
        else:
            result = hook_handle(('reprocess_action', args[0].type), args)
            if not result:
                print _('Sorry there is no available reprocessing for {}'
                        ' entries in the {} state'.format(args[0].type,
                                                          args[0].state))
    else:
        # Run media reprocessing
        return hook_handle(('media_reprocess', args[0].type), args)


def _set_media_state(args):
    """
    This will verify that all media id's are in the same state. If the
    --state flag is set, it will be replaced by the given media id's state.

    If they are trying to process different media states, an Exception will be
    raised.
    """
    if args[0].media_id:
        # Only check if we are given media_ids
        if len(args[0].media_id) == 1:
            args[0].state = MediaEntry.query.filter_by(id=args[0].media_id[0])\
                .first().state

        elif len(args[0].media_id) > 1:
            media_states = []

            for id in args[0].media_id:
                media_states.append(MediaEntry.query.filter_by(id=id).first()
                                    .state)

            # Make sure that all media are in the same state
            for state in media_states:
                if state != media_states[0]:
                    raise Exception(_('You can only reprocess media that is in'
                                      ' the same state.'))

            args[0].state = media_states[0]

    # If no state was set, then we will default to the processed state
    if not args[0].state:
        args[0].state = 'processed'


def available(args):
    # Get the media type, either by looking up media id, or by specific type
    
    ### TODO: look up by id

    #
    pass


def run(args):
    ### OLD CODE, review

    # Run eagerly unless explicetly set not to
    if not args.celery:
        os.environ['CELERY_ALWAYS_EAGER'] = 'true'
    commands_util.setup_app(args)

    _set_media_state(args)
    _set_media_type(args)

    # If no media_ids were given, then try to reprocess all entries
    if not args[0].media_id:
        return _reprocess_all(args)

    return _run_reprocessing(args)


def reprocess(args):
    if args.reprocess_subcommand == "run":
        run(args)
    elif args.reprocess_subcommand == "available":
        available(args)
