# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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


import code

from mediagoblin import mg_globals
from mediagoblin.gmg_commands import util as commands_util


def shell_parser_setup(subparser):
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help="Config file used to set up environment")


SHELL_BANNER = """\
GNU MediaGoblin shell!
----------------------
Available vars:
 - mgoblin_app: instantiated mediagoblin application
 - mg_globals: mediagoblin.globals
 - db: database instance
"""


def shell(args):
    """
    Setup a shell for the user
    """
    mgoblin_app = commands_util.setup_app(args)

    code.interact(
        banner=SHELL_BANNER,
        local={
            'mgoblin_app': mgoblin_app,
            'mg_globals': mg_globals,
            'db': mg_globals.database})
