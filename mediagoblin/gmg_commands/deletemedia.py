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

from mediagoblin.gmg_commands import util as commands_util


def parser_setup(subparser):
    subparser.add_argument('media_ids',
                           help='Comma separated list of media IDs to will be deleted.')


def deletemedia(args):
    app = commands_util.setup_app(args)

    media_ids = set(map(int, args.media_ids.split(',')))
    found_medias = set()
    filter_ids = app.db.MediaEntry.id.in_(media_ids)
    medias = app.db.MediaEntry.query.filter(filter_ids).all()
    for media in medias:
        found_medias.add(media.id)
        media.delete()
        print 'Media ID %d has been deleted.' % media.id
    for media in media_ids - found_medias:
        print 'Can\'t find a media with ID %d.' % media
    print 'Done.'
