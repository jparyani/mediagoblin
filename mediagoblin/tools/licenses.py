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

from collections import namedtuple
# Give a License attribute names: uri, name, abbreviation
License = namedtuple("License", ["abbreviation", "name", "uri"])

SORTED_LICENSES = [
    License("All rights reserved", "No license specified", ""),
    License("CC BY 3.0", "Creative Commons Attribution Unported 3.0",
           "http://creativecommons.org/licenses/by/3.0/"),
    License("CC BY-SA 3.0",
           "Creative Commons Attribution-ShareAlike Unported 3.0",
           "http://creativecommons.org/licenses/by-sa/3.0/"),
    License("CC BY-ND 3.0",
           "Creative Commons Attribution-NoDerivs 3.0 Unported",
           "http://creativecommons.org/licenses/by-nd/3.0/"),
    License("CC BY-NC 3.0",
          "Creative Commons Attribution-NonCommercial Unported 3.0",
          "http://creativecommons.org/licenses/by-nc/3.0/"),
    License("CC BY-NC-SA 3.0",
           "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported",
           "http://creativecommons.org/licenses/by-nc-sa/3.0/"),
    License("CC BY-NC-ND 3.0",
           "Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported",
           "http://creativecommons.org/licenses/by-nc-nd/3.0/"),
    License("CC0 1.0",
           "Creative Commons CC0 1.0 Universal",
           "http://creativecommons.org/publicdomain/zero/1.0/"),
    License("Public Domain","Public Domain",
           "http://creativecommons.org/publicdomain/mark/1.0/"),
    ]

# dict {uri: License,...} to enable fast license lookup by uri. Ideally,
# we'd want to use an OrderedDict (python 2.7+) here to avoid having the
# same data in two structures
SUPPORTED_LICENSES = dict(((l.uri, l) for l in SORTED_LICENSES))


def get_license_by_url(url):
    """Look up a license by its url and return the License object"""
    try:
        return SUPPORTED_LICENSES[url]
    except KeyError:
        # in case of an unknown License, just display the url given
        # rather than exploding in the user's face.
        return License(url, url, url)


def licenses_as_choices():
    """List of (uri, abbreviation) tuples for HTML choice field population

    The data seems to be consumed/deleted during usage, so hand over a
    throwaway list, rather than just a generator.
    """
    return [(lic.uri, lic.abbreviation) for lic in SORTED_LICENSES]
