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


def reprocess_parser_setup(subparser):
    subparser.add_argument(
        '--available', '-a',
        action="store_true",
        help="List available actions for a given media entry")
    subparser.add_argument(
        '--all', '-A',
        action="store_true",
        help="Reprocess all media entries")
    subparser.add_argument(
        '--state', '-s',
        help="Reprocess media entries in this state"
             " such as 'failed' or 'processed'")
    subparser.add_argument(
        '--type', '-t',
        help="The type of media to be reprocessed such as 'video' or 'image'")
    subparser.add_argument(
        'media_id',
        nargs='*',
        help="The media_entry id(s) you wish to reprocess.")


def reprocess(args):
    pass
