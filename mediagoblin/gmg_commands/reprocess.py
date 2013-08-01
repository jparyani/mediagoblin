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
from mediagoblin.db.models import MediaEntry
from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.tools.pluginapi import hook_handle


def reprocess_parser_setup(subparser):
    subparser.add_argument(
        '--available', '-a',
        action="store_true",
        help="List available actions for a given media entry")
    subparser.add_argument(
        '--state', '-s',
        help="Reprocess media entries in this state"
             " such as 'failed' or 'processed'")
    subparser.add_argument(
        '--type', '-t',
        help="The type of media to be reprocessed such as 'video' or 'image'")
    subparser.add_argument(
        '--media_id',
        nargs='*',
        help="The media_entry id(s) you wish to reprocess.")


def _set_media_type(args):
    if args[0].media_id:
        if len(args[0].media_id) == 1:
            media_type = MediaEntry.query.filter_by(id=args[0].media_id[0])\
                .first().media_type.split('.')[-1]

            if not args[0].type:
                args[0].type = media_type
            elif args[0].type != media_type:
                raise Exception(_('The --type that you set does not match the type'
                                ' of the given media_id.'))
        elif len(args[0].media_id) > 1:
            media_types = []

            for id in args[0].media_id:
                media_types.append(MediaEntry.query.filter_by(id=id).first()
                                .media_type.split('.')[-1])
            for type in media_types:
                if media_types[0] != type:
                    raise Exception((u'You cannot reprocess different media_types'
                                    ' at the same time.'))

            if not args[0].type:
                args[0].type = media_types[0]
            elif args[0].type != media_types[0]:
                raise Exception(_('The --type that you set does not match the type'
                                ' of the given media_ids.'))


def _reprocess_all(args):
    if not args[0].type:
        if args[0].state == 'failed':
            if args[0].available:
                print _('\n Available reprocess actions for all failed'
                        ' media_entries: \n \t --initial_processing')
                return
            else:
                #TODO reprocess all failed entries
                pass
        else:
            raise Exception(_('You must set --type when trying to reprocess'
                              ' all media_entries, unless you set --state'
                              ' to "failed".'))

    _run_reprocessing(args)


def _run_reprocessing(args):
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
        return hook_handle(('media_reprocess', args[0].type), args)


def _set_media_state(args):
    if args[0].media_id:
        if len(args[0].media_id) == 1:
            args[0].state = MediaEntry.query.filter_by(id=args[0].media_id[0])\
                .first().state

        elif len(args[0].media_id) > 1:
            media_states = []

            for id in args[0].media_id:
                media_states.append(MediaEntry.query.filter_by(id=id).first()
                                    .state)
            for state in media_states:
                if state != media_states[0]:
                    raise Exception(_('You can only reprocess media that is in the'
                                    ' same state.'))

            args[0].state = media_states[0]

    if not args[0].state:
        args[0].state = 'processed'


def reprocess(args):
    commands_util.setup_app(args[0])

    _set_media_state(args)
    _set_media_type(args)

    if not args[0].media_id:
        return _reprocess_all(args)

    return _run_reprocessing(args)
