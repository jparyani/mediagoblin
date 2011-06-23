# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

import jinja2


def get_jinja_loader(user_template_path=None):
    """
    Set up the Jinja template loaders, possibly allowing for user
    overridden templates.

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    if user_template_path:
        return jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(user_template_path),
             jinja2.PackageLoader('mediagoblin', 'templates')])
    else:
        return jinja2.PackageLoader('mediagoblin', 'templates')
