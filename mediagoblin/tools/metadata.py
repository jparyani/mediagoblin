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
import copy
import json
import re
from pkg_resources import resource_filename

import dateutil.parser
from pyld import jsonld
from jsonschema import validate, FormatChecker, draft4_format_checker
from jsonschema.compat import str_types


MEDIAGOBLIN_CONTEXT_PATH = resource_filename(
    "mediagoblin",
    os.path.sep.join(["static", "metadata", "mediagoblin-0.1.dev.jsonld"]))
MEDIAGOBLIN_CONTEXT = json.loads(file(MEDIAGOBLIN_CONTEXT_PATH).read())


########################################################
## Set up the MediaGoblin format checker for json-schema
########################################################

URL_REGEX = re.compile(
    r'^[a-z]+://([^/:]+|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$',
    re.IGNORECASE)

def is_uri(instance):
    """
    jsonschema uri validator
    """
    if not isinstance(instance, str_types):
        return True

    return URL_REGEX.match(instance)

def is_datetime(instance):
    """
    Is a date or datetime readable string.
    """
    if not isinstance(instance, str_types):
        return True

    return dateutil.parser.parse(instance)


class DefaultChecker(FormatChecker):
    """
    Default MediaGoblin format checker... extended to include a few extra things
    """
    checkers = copy.deepcopy(draft4_format_checker.checkers)


DefaultChecker.checkers[u"uri"] = (is_uri, ())
DefaultChecker.checkers[u"date-time"] = (is_datetime, (ValueError, TypeError))
DEFAULT_CHECKER = DefaultChecker()

# Crappy default schema, checks for things we deem important

DEFAULT_SCHEMA = {
    "$schema": "http://json-schema.org/schema#",

    "type": "object",
    "properties": {
        "license": {
            "format": "uri",
            "type": "string",
        },
        "dcterms:created": {
            "format": "date-time",
            "type": "string",
        }
    },
}


def compact_and_validate(metadata, context=MEDIAGOBLIN_CONTEXT,
                         schema=DEFAULT_SCHEMA):
    """
    compact json with supplied context, check against schema for errors

    raises an exception (jsonschema.exceptions.ValidationError) if
    there's an error.9

    You may wish to do this validation yourself... this is just for convenience.
    """
    compacted = jsonld.compact(metadata, context)
    validate(metadata, schema, format_checker=DEFAULT_CHECKER)

    return compacted
