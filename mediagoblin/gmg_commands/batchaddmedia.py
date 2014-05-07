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
import copy, tempfile, tarfile, zipfile, subprocess, re, requests
from csv import reader as csv_reader
from urlparse import urlparse
from pyld import jsonld

from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.submit.lib import (
    submit_media, get_upload_file_limits,
    FileUploadLimit, UserUploadLimit, UserPastUploadLimit)
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

from mediagoblin import mg_globals
from jsonschema import validate, FormatChecker, draft4_format_checker
from jsonschema.exceptions import ValidationError
from jsonschema.compat import str_types


def parser_setup(subparser):
    subparser.description = """\
This command allows the administrator to upload many media files at once."""
    subparser.add_argument(
        'username',
        help="Name of user these media entries belong to")
    subparser.add_argument(
        'target_path',
        help=("""\
Path to a local archive or directory containing a "location.csv" and a 
"metadata.csv" file. These are csv (comma seperated value) files with the
locations and metadata of the files to be uploaded. The location must be listed
with either the URL of the remote media file or the filesystem path of a local
file. The metadata should be provided with one column for each of the 15 Dublin
Core properties (http://dublincore.org/documents/dces/). Both "location.csv" and
"metadata.csv" must begin with a row demonstrating the order of the columns. We
have provided an example of these files at <url to be added>
"""))
    subparser.add_argument(
        '--celery',
        action='store_true',
        help="Don't process eagerly, pass off to celery")


def batchaddmedia(args):
    # Run eagerly unless explicetly set not to
    if not args.celery:
        os.environ['CELERY_ALWAYS_EAGER'] = 'true'

    app = commands_util.setup_app(args)

    files_uploaded, files_attempted = 0, 0

    # get the user
    user = app.db.User.query.filter_by(username=args.username.lower()).first()
    if user is None:
        print "Sorry, no user by username '%s' exists" % args.username
        return

    upload_limit, max_file_size = get_upload_file_limits(user)
    temp_files = []

    if os.path.isdir(args.target_path):
        dir_path = args.target_path

    elif tarfile.is_tarfile(args.target_path):
        dir_path = tempfile.mkdtemp()
        temp_files.append(dir_path)
        tar = tarfile.open(args.target_path)
        tar.extractall(path=dir_path)

    elif zipfile.is_zipfile(args.target_path):
        dir_path = tempfile.mkdtemp()
        temp_files.append(dir_path)
        zipped_file = zipfile.ZipFile(args.target_path)
        zipped_file.extractall(path=dir_path)

    else:
        print "Couldn't recognize the file. This script only accepts tar files,\
zip files and directories"
    if dir_path.endswith('/'):
        dir_path = dir_path[:-1]

    location_file_path = os.path.join(dir_path,"location.csv")
    metadata_file_path = os.path.join(dir_path, "metadata.csv")

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

    metadata_context = { 'dcterms':'http://purl.org/dc/terms/',
                         'xsd': 'http://www.w3.org/2001/XMLSchema#'}

    for media_id in media_locations.keys():
        files_attempted += 1

        file_metadata     = media_metadata[media_id]
        sanitized_metadata = check_metadata_format(file_metadata)
        if sanitized_metadata == {}: continue

        json_ld_metadata = jsonld.compact(build_json_ld_metadata(file_metadata), 
                                            metadata_context)
        original_location = media_locations[media_id]['media:original']
        url = urlparse(original_location)

        title = sanitized_metadata.get('dcterms:title')
        description = sanitized_metadata.get('dcterms:description')

        # TODO: this isn't the same thing
        license = sanitized_metadata.get('dcterms:rights')
        filename = url.path.split()[-1]

        if url.scheme == 'http':
            res = requests.get(url.geturl(), stream=True)
            media_file = res.raw

        elif url.scheme == '':
            path = url.path
            if os.path.isabs(path):
                file_abs_path = os.path.abspath(path)
            else:
                file_path = os.path.join(dir_path, path)
                file_abs_path = os.path.abspath(file_path)
            try:
                media_file = file(file_abs_path, 'r')
            except IOError:
                print "\
FAIL: Local file {filename} could not be accessed.".format(filename=filename)
                print "Skipping it."
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
            print "Successfully uploading {filename}!".format(filename=filename)
            print ""
            files_uploaded += 1
        except FileUploadLimit:
            print "FAIL: This file is larger than the upload limits for this site."
        except UserUploadLimit:
            print "FAIL: This file will put this user past their upload limits."
        except UserPastUploadLimit:
            print "FAIL: This user is already past their upload limits."
    print "\
{files_uploaded} out of {files_attempted} files successfully uploaded".format(
        files_uploaded=files_uploaded,
        files_attempted=files_attempted)
    teardown(temp_files)


def parse_csv_file(file_contents):
    list_of_contents = file_contents.split('\n')
    key, lines = (list_of_contents[0].split(','),
                  list_of_contents[1:])
    objects_dict = {}

    # Build a dictionaryfrom mediagoblin.tools.translate import lazy_pass_to_ugettext as _
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

def build_json_ld_metadata(metadata_dict):
    output_dict = {}
    for p in metadata_dict.keys():
        if p in ["dcterms:rights", "dcterms:relation"]:
            m_type = "xsd:uri"
        elif p in ["dcterms:date", "dcterms:created"]:
            m_type = "xsd:date"
        else:
            m_type = "xsd:string"
        description = {"@value": metadata_dict[p],
                       "@type" : m_type}
        output_dict[p] = description
    return output_dict


## Set up the MediaGoblin checker
# 

URL_REGEX = re.compile(
    r'^[a-z]+://([^/:]+|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$',
    re.IGNORECASE)

def is_uri(instance):
    if not isinstance(instance, str_types):
        return True

    return URL_REGEX.match(instance)


class DefaultChecker(FormatChecker):
    checkers = copy.deepcopy(draft4_format_checker.checkers)

DefaultChecker.checkers[u"uri"] = (is_uri, ())

DEFAULT_CHECKER = DefaultChecker()

def check_metadata_format(metadata_dict):
    schema = {
        "$schema": "http://json-schema.org/schema#",

        "type": "object",
        "properties": {
            "dcterms:rights": {
                "format": "uri",
                "type": "string",
            },
            "dcterms:created": {
                
            }
        },
        # "required": ["dcterms:title", "media:id"],
    }

    try:
        validate(metadata_dict, schema,
                 format_checker=DEFAULT_CHECKER)
        output_dict = metadata_dict
        # "media:id" is only for internal use, so we delete it for the output
        del output_dict['media:id']

    except ValidationError, exc:
        title = (metadata_dict.get('dcterms:title') or 
            metadata_dict.get('media:id') or _(u'UNKNOWN FILE'))

        if exc.validator == "additionalProperties":
            message = _(u'Invalid metadata provided for file "{title}". This \
script only accepts the Dublin Core metadata terms.'.format(title=title))

        elif exc.validator == "required":
            message = _(
u'All necessary metadata was not provided for file "{title}", you must include \
a "dcterms:title" column for each media file'.format(title=title))

        else:
            message = _(u'Could not find appropriate metadata for file \
"{title}".'.format(title=title))

        print _(u"""WARN: {message} \nSkipping File...\n""".format(
            message=message))

        output_dict = {}
    except:
        raise

    return output_dict
