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


from mediagoblin import app
import getpass


def setup_app(args):
    """
    Setup the application after reading the mediagoblin config files
    """
    mgoblin_app = app.MediaGoblinApp(args.conf_file)

    return mgoblin_app

def prompt_if_not_set(variable, text, password=False):
    """
    Checks if the variable is None and prompt for a value if it is
    """
    if variable is None:
        if not password:
            variable=raw_input(text + u' ')
        else:
            variable=getpass.getpass(text + u' ')

    return variable
