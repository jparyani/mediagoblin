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

import codecs
import csv
import os

import requests
import six

from six.moves.urllib.parse import urlparse

from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.submit.lib import (
    submit_media, get_upload_file_limits,
    FileUploadLimit, UserUploadLimit, UserPastUploadLimit)
from mediagoblin.tools.metadata import compact_and_validate
from mediagoblin.tools.translate import pass_to_ugettext as _
from jsonschema.exceptions import ValidationError


def parser_setup(subparser):
    subparser.description = """\
This command allows the administrator to upload many media files at once."""
    subparser.epilog = _(u"""For more information about how to properly run this
script (and how to format the metadata csv file), read the MediaGoblin
documentation page on command line uploading
<http://docs.mediagoblin.org/siteadmin/commandline-upload.html>""")
    subparser.add_argument(
        'username',
        help=_(u"Name of user these media entries belong to"))
    subparser.add_argument(
        'metadata_path',
        help=_(
u"""Path to the csv file containing metadata information."""))
    subparser.add_argument(
        '--celery',
        action='store_true',
        help=_(u"Don't process eagerly, pass off to celery"))


def batchaddmedia(args):
    # Run eagerly unless explicetly set not to
    if not args.celery:
        os.environ['CELERY_ALWAYS_EAGER'] = 'true'

    app = commands_util.setup_app(args)

    files_uploaded, files_attempted = 0, 0

    # get the user
    user = app.db.User.query.filter_by(username=args.username.lower()).first()
    if user is None:
        print(_(u"Sorry, no user by username '{username}' exists".format(
                    username=args.username)))
        return

    upload_limit, max_file_size = get_upload_file_limits(user)
    temp_files = []

    if os.path.isfile(args.metadata_path):
        metadata_path = args.metadata_path

    else:
        error = _(u'File at {path} not found, use -h flag for help'.format(
                    path=args.metadata_path))
        print(error)
        return

    abs_metadata_filename = os.path.abspath(metadata_path)
    abs_metadata_dir = os.path.dirname(abs_metadata_filename)
    upload_limit, max_file_size = get_upload_file_limits(user)

    def maybe_unicodeify(some_string):
        # this is kinda terrible
        if some_string is None:
            return None
        else:
            return six.text_type(some_string)

    with codecs.open(
            abs_metadata_filename, 'r', encoding='utf-8') as all_metadata:
        contents = all_metadata.read()
        media_metadata = parse_csv_file(contents)

    for media_id, file_metadata in media_metadata.iteritems():
        files_attempted += 1
        # In case the metadata was not uploaded initialize an empty dictionary.
        json_ld_metadata = compact_and_validate({})

        # Get all metadata entries starting with 'media' as variables and then
        # delete them because those are for internal use only.
        original_location = file_metadata['location']

        ### Pull the important media information for mediagoblin from the
        ### metadata, if it is provided.
        title = file_metadata.get('title') or file_metadata.get('dc:title')
        description = (file_metadata.get('description') or
            file_metadata.get('dc:description'))

        license = file_metadata.get('license')
        try:
            json_ld_metadata = compact_and_validate(file_metadata)
        except ValidationError as exc:
            error = _(u"""Error with media '{media_id}' value '{error_path}': {error_msg}
Metadata was not uploaded.""".format(
                media_id=media_id,
                error_path=exc.path[0],
                error_msg=exc.message))
            print(error)
            continue

        url = urlparse(original_location)
        filename = url.path.split()[-1]

        if url.scheme == 'http':
            res = requests.get(url.geturl(), stream=True)
            media_file = res.raw

        elif url.scheme == '':
            path = url.path
            if os.path.isabs(path):
                file_abs_path = os.path.abspath(path)
            else:
                file_path = os.path.join(abs_metadata_dir, path)
                file_abs_path = os.path.abspath(file_path)
            try:
                media_file = file(file_abs_path, 'r')
            except IOError:
                print(_(u"""\
FAIL: Local file {filename} could not be accessed.
{filename} will not be uploaded.""".format(filename=filename)))
                continue
        try:
            submit_media(
                mg_app=app,
                user=user,
                submitted_file=media_file,
                filename=filename,
                title=maybe_unicodeify(title),
                description=maybe_unicodeify(description),
                license=maybe_unicodeify(license),
                metadata=json_ld_metadata,
                tags_string=u"",
                upload_limit=upload_limit, max_file_size=max_file_size)
            print(_(u"""Successfully submitted {filename}!
Be sure to look at the Media Processing Panel on your website to be sure it
uploaded successfully.""".format(filename=filename)))
            files_uploaded += 1
        except FileUploadLimit:
            print(_(
u"FAIL: This file is larger than the upload limits for this site."))
        except UserUploadLimit:
            print(_(
"FAIL: This file will put this user past their upload limits."))
        except UserPastUploadLimit:
            print(_("FAIL: This user is already past their upload limits."))
    print(_(
"{files_uploaded} out of {files_attempted} files successfully submitted".format(
        files_uploaded=files_uploaded,
        files_attempted=files_attempted)))


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def parse_csv_file(file_contents):
    """
    The helper function which converts the csv file into a dictionary where each
    item's key is the provided value 'id' and each item's value is another
    dictionary.
    """
    list_of_contents = file_contents.split('\n')
    key, lines = (list_of_contents[0].split(','),
                  list_of_contents[1:])
    objects_dict = {}

    # Build a dictionary
    for index, line in enumerate(lines):
        if line.isspace() or line == u'': continue
        values = unicode_csv_reader([line]).next()
        line_dict = dict([(key[i], val)
            for i, val in enumerate(values)])
        media_id = line_dict.get('id') or index
        objects_dict[media_id] = (line_dict)

    return objects_dict

