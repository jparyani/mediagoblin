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


import code

from mediagoblin import mg_globals
from mediagoblin.gmg_commands import util as commands_util


def shell_parser_setup(subparser):
    subparser.add_argument(
        '--ipython', help='Use ipython',
        action="store_true")


SHELL_BANNER = """\
GNU MediaGoblin shell!
----------------------
Available vars:
 - mgoblin_app: instantiated mediagoblin application
 - mg_globals: mediagoblin.globals
 - db: database instance
"""

def py_shell(**user_namespace):
    """
    Run a shell using normal python shell.
    """
    code.interact(
        banner=SHELL_BANNER,
        local=user_namespace)


def ipython_shell(**user_namespace):
    """
    Run a shell for the user using ipython. Return False if there is no IPython
    """
    try:
        from IPython import embed
    except:
        return False

    embed(
        banner1=SHELL_BANNER,
        user_ns=user_namespace)
    return True

def shell(args):
    """
    Setup a shell for the user either a normal Python shell or an IPython one
    """
    user_namespace = {
        'mg_globals': mg_globals,
        'mgoblin_app': commands_util.setup_app(args),
        'db': mg_globals.database}

    if args.ipython:
        ipython_shell(**user_namespace)
    else:
        # Try ipython_shell first and fall back if not available
        if not ipython_shell(**user_namespace):
            py_shell(**user_namespace)
