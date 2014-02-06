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

import os

from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.submit.lib import (
    submit_media, get_upload_file_limits,
    FileUploadLimit, UserUploadLimit, UserPastUploadLimit)

from mediagoblin import mg_globals
import json, csv

def parser_setup(subparser):
    subparser.add_argument(
        'username',
        help="Name of user this media entry belongs to")
    subparser.add_argument(
        'locationfile',
        help=(
"Local file on filesystem with the address of all the files to be uploaded"))
    subparser.add_argument(
        'metadatafile',
        help=(
"Local file on filesystem with metadata of all the files to be uploaded"))
    subparser.add_argument(
        "-l", "--license",
        help=(
            "License these media entry will be released under, if all the same"
            "Should be a URL."))
    subparser.add_argument(
        '--celery',
        action='store_true',
        help="Don't process eagerly, pass off to celery")


def batchaddmedia(args):
    # Run eagerly unless explicetly set not to
    if not args.celery:
        os.environ['CELERY_ALWAYS_EAGER'] = 'true'

    app = commands_util.setup_app(args)

    # get the user
    user = app.db.User.query.filter_by(username=args.username.lower()).first()
    if user is None:
        print "Sorry, no user by username '%s'" % args.username
        return
    
    # check for the location file, if it exists...
    location_filename = os.path.split(args.locationfile)[-1]
    abs_location_filename = os.path.abspath(args.locationfile)
    if not os.path.exists(abs_location_filename):
        print "Can't find a file with filename '%s'" % args.locationfile
        return

    # check for the location file, if it exists...
    metadata_filename = os.path.split(args.metadatafile)[-1]
    abs_metadata_filename = os.path.abspath(args.metadatafile)
    if not os.path.exists(abs_metadata_filename):
        print "Can't find a file with filename '%s'" % args.metadatafile
        return

    upload_limit, max_file_size = get_upload_file_limits(user)

    def maybe_unicodeify(some_string):
        # this is kinda terrible
        if some_string is None:
            return None
        else:
            return unicode(some_string)

    with file(abs_location_filename, 'r') as all_locations:
        contents = all_locations.read()
        media_locations = parse_csv_file(contents)

    with file(abs_metadata_filename, 'r') as all_metadata:
        contents = all_metadata.read()
        media_metadata = parse_csv_file(contents)

def parse_csv_file(file_contents):
    list_of_contents = file_contents.split('\n')
    key, lines = (list_of_contents[0].split(','),
                  list_of_contents[1:])
    list_of_objects = []

    # Build a dictionary
    for line in lines:
        if line.isspace() or line == '': continue
        values = csv.reader([line]).next()
        new_dict = dict([(key[i], val)
            for i, val in enumerate(values)])
        list_of_objects.append(new_dict)

    return list_of_objects

    
