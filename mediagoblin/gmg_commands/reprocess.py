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

from __future__ import print_function

import argparse
import os

from mediagoblin import mg_globals
from mediagoblin.db.models import MediaEntry
from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.submit.lib import run_process_media
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.tools.pluginapi import hook_handle
from mediagoblin.processing import (
    ProcessorDoesNotExist, ProcessorNotEligible,
    get_entry_and_processing_manager, get_processing_manager_for_type,
    ProcessingManagerDoesNotExist)


def reprocess_parser_setup(subparser):
    subparser.add_argument(
        '--celery',
        action='store_true',
        help="Don't process eagerly, pass off to celery")

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

    available_parser.add_argument(
        "--action-help",
        action="store_true",
        help="List argument help for each action available")

    available_parser.add_argument(
        "--state",
        help="The state of media you would like to reprocess")


    #############
    # run command
    #############

    run_parser = subparsers.add_parser(
        "run",
        help="Run a reprocessing on one or more media")

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


    ################
    # thumbs command
    ################
    thumbs = subparsers.add_parser(
        'thumbs',
        help='Regenerate thumbs for all processed media')

    thumbs.add_argument(
        '--size',
        nargs=2,
        type=int,
        metavar=('max_width', 'max_height'))

    #################
    # initial command
    #################
    subparsers.add_parser(
        'initial',
        help='Reprocess all failed media')

    ##################
    # bulk_run command
    ##################
    bulk_run_parser = subparsers.add_parser(
        'bulk_run',
        help='Run reprocessing on a given media type or state')

    bulk_run_parser.add_argument(
        'type',
        help='The type of media you would like to process')

    bulk_run_parser.add_argument(
        '--state',
        default='processed',
        nargs='?',
        help='The state of the media you would like to process. Defaults to' \
             " 'processed'")

    bulk_run_parser.add_argument(
        'reprocess_command',
        help='The reprocess command you intend to run')

    bulk_run_parser.add_argument(
        'reprocess_args',
        nargs=argparse.REMAINDER,
        help='The rest of the arguments to the reprocessing tool')

    ###############
    # help command?
    ###############


def available(args):
    # Get the media type, either by looking up media id, or by specific type
    try:
        media_id = int(args.id_or_type)
        media_entry, manager = get_entry_and_processing_manager(media_id)
        media_type = media_entry.media_type
    except ValueError:
        media_type = args.id_or_type
        media_entry = None
        manager = get_processing_manager_for_type(media_type)
    except ProcessingManagerDoesNotExist:
        entry = MediaEntry.query.filter_by(id=args.id_or_type).first()
        print('No such processing manager for {0}'.format(entry.media_type))

    if args.state:
        processors = manager.list_all_processors_by_state(args.state)
    elif media_entry is None:
        processors = manager.list_all_processors()
    else:
        processors = manager.list_eligible_processors(media_entry)

    print("Available processors:")
    print("=====================")
    print("")

    if args.action_help:
        for processor in processors:
            print(processor.name)
            print("-" * len(processor.name))

            parser = processor.generate_parser()
            parser.print_help()
            print("")

    else:
        for processor in processors:
            if processor.description:
                print(" - %s: %s" % (processor.name, processor.description))
            else:
                print(" - %s" % processor.name)


def run(args, media_id=None):
    if not media_id:
        media_id = args.media_id
    try:
        media_entry, manager = get_entry_and_processing_manager(media_id)

        # TODO: (maybe?) This could probably be handled entirely by the
        # processor class...
        try:
            processor_class = manager.get_processor(
                args.reprocess_command, media_entry)
        except ProcessorDoesNotExist:
            print('No such processor "%s" for media with id "%s"' % (
                args.reprocess_command, media_entry.id))
            return
        except ProcessorNotEligible:
            print('Processor "%s" exists but media "%s" is not eligible' % (
                args.reprocess_command, media_entry.id))
            return

        reprocess_parser = processor_class.generate_parser()
        reprocess_args = reprocess_parser.parse_args(args.reprocess_args)
        reprocess_request = processor_class.args_to_request(reprocess_args)
        run_process_media(
            media_entry,
            reprocess_action=args.reprocess_command,
            reprocess_info=reprocess_request)

    except ProcessingManagerDoesNotExist:
        entry = MediaEntry.query.filter_by(id=media_id).first()
        print('No such processing manager for {0}'.format(entry.media_type))


def bulk_run(args):
    """
    Bulk reprocessing of a given media_type
    """
    query = MediaEntry.query.filter_by(media_type=args.type,
                                       state=args.state)

    for entry in query:
        run(args, entry.id)


def thumbs(args):
    """
    Regenerate thumbs for all processed media
    """
    query = MediaEntry.query.filter_by(state='processed')

    for entry in query:
        try:
            media_entry, manager = get_entry_and_processing_manager(entry.id)

            # TODO: (maybe?) This could probably be handled entirely by the
            # processor class...
            try:
                processor_class = manager.get_processor(
                    'resize', media_entry)
            except ProcessorDoesNotExist:
                print('No such processor "%s" for media with id "%s"' % (
                    'resize', media_entry.id))
                return
            except ProcessorNotEligible:
                print('Processor "%s" exists but media "%s" is not eligible' % (
                    'resize', media_entry.id))
                return

            reprocess_parser = processor_class.generate_parser()

            # prepare filetype and size to be passed into reprocess_parser
            if args.size:
                extra_args = 'thumb --{0} {1} {2}'.format(
                    processor_class.thumb_size,
                    args.size[0],
                    args.size[1])
            else:
                extra_args = 'thumb'

            reprocess_args = reprocess_parser.parse_args(extra_args.split())
            reprocess_request = processor_class.args_to_request(reprocess_args)
            run_process_media(
                media_entry,
                reprocess_action='resize',
                reprocess_info=reprocess_request)

        except ProcessingManagerDoesNotExist:
            print('No such processing manager for {0}'.format(entry.media_type))


def initial(args):
    """
    Reprocess all failed media
    """
    query = MediaEntry.query.filter_by(state='failed')

    for entry in query:
        try:
            media_entry, manager = get_entry_and_processing_manager(entry.id)
            run_process_media(
                media_entry,
                reprocess_action='initial')
        except ProcessingManagerDoesNotExist:
            print('No such processing manager for {0}'.format(entry.media_type))


def reprocess(args):
    # Run eagerly unless explicetly set not to
    if not args.celery:
        os.environ['CELERY_ALWAYS_EAGER'] = 'true'

    commands_util.setup_app(args)

    if args.reprocess_subcommand == "run":
        run(args)

    elif args.reprocess_subcommand == "available":
        available(args)

    elif args.reprocess_subcommand == "bulk_run":
        bulk_run(args)

    elif args.reprocess_subcommand == "thumbs":
        thumbs(args)

    elif args.reprocess_subcommand == "initial":
        initial(args)
