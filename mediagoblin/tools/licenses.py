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

SORTED_SUPPORTED_LICENSES = [
    ("",
     {"name": "No license specified",
      "abbreviation": "All rights reserved"}),
    ("http://creativecommons.org/licenses/by/3.0/",
     {"name": "Creative Commons Attribution Unported 3.0",
      "abbreviation": "CC BY 3.0"}),
    ("http://creativecommons.org/licenses/by-sa/3.0/",
     {"name": "Creative Commons Attribution-ShareAlike Unported 3.0",
      "abbreviation": "CC BY-SA 3.0"}),
    ("http://creativecommons.org/licenses/by-nd/3.0/",
     {"name": "Creative Commons Attribution-NoDerivs 3.0 Unported",
      "abbreviation": "CC BY-ND 3.0"}),
    ("http://creativecommons.org/licenses/by-nc/3.0/",
     {"name": "Creative Commons Attribution-NonCommercial Unported 3.0",
      "abbreviation": "CC BY-NC 3.0"}),
    ("http://creativecommons.org/licenses/by-nc-sa/3.0/",
     {"name": "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported",
      "abbreviation": "CC BY-NC-SA 3.0"}),
    ("http://creativecommons.org/licenses/by-nc-nd/3.0/",
     {"name": "Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported",
      "abbreviation": "CC BY-NC-ND 3.0"}),
    ("http://creativecommons.org/publicdomain/zero/1.0/",
     {"name": "Creative Commons CC0 1.0 Universal",
      "abbreviation": "CC0 1.0"}),
    ("http://creativecommons.org/publicdomain/mark/1.0/",
     {"name": "Public Domain",
      "abbreviation": "Public Domain"})]

SUPPORTED_LICENSES = dict(SORTED_SUPPORTED_LICENSES)


def licenses_as_choices():
    license_list = []

    for uri, data in SORTED_SUPPORTED_LICENSES:
        license_list.append((uri, data["abbreviation"]))

    return license_list
