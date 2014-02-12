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
import json, tempfile, urllib, tarfile, subprocess
from csv import reader as csv_reader
from urlparse import urlparse
from pyld import jsonld

from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.submit.lib import (
    submit_media, get_upload_file_limits,
    FileUploadLimit, UserUploadLimit, UserPastUploadLimit)

from mediagoblin import mg_globals

def parser_setup(subparser):
    subparser.add_argument(
        'username',
        help="Name of user this media entry belongs to")
    target_type = subparser.add_mutually_exclusive_group()
    target_type.add_argument('-d',
        '--directory', action='store_const',
        const='directory', dest='target_type', 
        default='directory', help=(
"Target is a directory"))
    target_type.add_argument('-a',
        '--archive', action='store_const',
        const='archive', dest='target_type',
        help=(
"Target is an archive."))
    subparser.add_argument(
        'target_path',
        help=(
"Path to a local archive or directory containing a location.csv and metadata.csv file"))
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

    upload_limit, max_file_size = get_upload_file_limits(user)
    temp_files = []

    if args.target_type == 'archive':
        dir_path = tempfile.mkdtemp()
        temp_files.append(dir_path)
        tar = tarfile.open(args.target_path)
        tar.extractall(path=dir_path)

    elif args.target_type == 'directory':
        dir_path = args.target_path

    location_file_path = "{dir_path}/location.csv".format(
        dir_path=dir_path)
    metadata_file_path = "{dir_path}/metadata.csv".format(
        dir_path=dir_path)
    
    # check for the location file, if it exists...
    location_filename = os.path.split(location_file_path)[-1]
    abs_location_filename = os.path.abspath(location_file_path)
    if not os.path.exists(abs_location_filename):
        print "Can't find a file with filename '%s'" % location_file_path
        return

    # check for the metadata file, if it exists...
    metadata_filename = os.path.split(metadata_file_path)[-1]
    abs_metadata_filename = os.path.abspath(metadata_file_path)
    if not os.path.exists(abs_metadata_filename):
        print "Can't find a file with filename '%s'" % metadata_file_path
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

    dcterms_context = { 'dcterms':'http://purl.org/dc/terms/' }

    for media_id in media_locations.keys():
        file_metadata = media_metadata[media_id]
        json_ld_metadata = jsonld.compact(file_metadata, dcterms_context)
        original_location = media_locations[media_id]['media:original']
        url = urlparse(original_location)

        title = file_metadata.get('dcterms:title')
        description = file_metadata.get('dcterms:description')
        license = file_metadata.get('dcterms:license')
        filename = url.path.split()[-1]
        print "Working with {filename}".format(filename=filename)

        if url.scheme == 'http':
            print "Downloading {filename}...".format(
                filename=filename)
            media_file = tempfile.TemporaryFile()
            res = urllib.urlopen(url.geturl())
            media_file.write(res.read())
            media_file.seek(0)

        elif url.scheme == '':
            path = url.path
            if os.path.isabs(path):
                file_abs_path = os.path.abspath(path)
            else:
                file_path = "{dir_path}/{local_path}".format(
                    dir_path=dir_path,
                    local_path=path)
                file_abs_path = os.path.abspath(file_path)
            try:
                media_file = file(file_abs_path, 'r')
            except IOError:
                print "Local file {filename} could not be accessed.".format(
                    filename=filename)
                print "Skipping it."
                continue
        print "Submitting {filename}...".format(filename=filename)
        try:
            submit_media(
                mg_app=app,
                user=user,
                submitted_file=media_file,
                filename=filename,
                title=maybe_unicodeify(title),
                description=maybe_unicodeify(description),
                license=maybe_unicodeify(license),
                tags_string=u"",
                upload_limit=upload_limit, max_file_size=max_file_size)
            print "Successfully uploading {filename}!".format(filename=filename)
            print ""
        except FileUploadLimit:
            print "This file is larger than the upload limits for this site."
        except UserUploadLimit:
            print "This file will put this user past their upload limits."
        except UserPastUploadLimit:
            print "This user is already past their upload limits."
    teardown(temp_files)

        

def parse_csv_file(file_contents):
    list_of_contents = file_contents.split('\n')
    key, lines = (list_of_contents[0].split(','),
                  list_of_contents[1:])
    objects_dict = {}

    # Build a dictionary
    for line in lines:
        if line.isspace() or line == '': continue
        values = csv_reader([line]).next()
        line_dict = dict([(key[i], val)
            for i, val in enumerate(values)])
        media_id = line_dict['media:id']
        objects_dict[media_id] = (line_dict)

    return objects_dict

def teardown(temp_files):
    for temp_file in temp_files:
        subprocess.call(['rm','-r',temp_file])
