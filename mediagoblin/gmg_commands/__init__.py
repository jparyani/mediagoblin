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

import code
import argparse
import os

from paste.deploy.loadwsgi import NicerConfigParser

from mediagoblin.celery_setup import setup_celery_from_config
from mediagoblin import app, util
from mediagoblin import globals as mgoblin_globals


SUBCOMMAND_MAP = {
    'shell': {
        'setup': 'mediagoblin.gmg_commands:shell_parser_setup',
        'func': 'mediagoblin.gmg_commands:shell',
        'help': 'Run a shell with some tools pre-setup'},
    }


def shell_parser_setup(subparser):
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help="Config file used to set up environment")
    subparser.add_argument(
        '-cs', '--app_section', default='app:mediagoblin',
        help="Section of the config file where the app config is stored.")


SHELL_BANNER = """\
GNU MediaGoblin shell!
----------------------
Available vars:
 - mgoblin_app: instantiated mediagoblin application
 - mgoblin_globals: mediagoblin.globals
 - db: database instance
"""


def shell(args):
    """
    """
    # Duplicated from from_celery.py, remove when we have the generic util
    parser = NicerConfigParser(args.conf_file)
    parser.read(args.conf_file)
    parser._defaults.setdefault(
        'here', os.path.dirname(os.path.abspath(args.conf_file)))
    parser._defaults.setdefault(
        '__file__', os.path.abspath(args.conf_file))

    mgoblin_section = dict(parser.items(args.app_section))
    mgoblin_conf = dict(
        [(section_name, dict(parser.items(section_name)))
         for section_name in parser.sections()])

    mgoblin_app = app.paste_app_factory(
        mgoblin_conf, **mgoblin_section)

    code.interact(
        banner=SHELL_BANNER,
        local={
            'mgoblin_app': mgoblin_app,
            'mgoblin_globals': mgoblin_globals,
            'db': mgoblin_globals.database})
    

def main_cli():
    parser = argparse.ArgumentParser(
        description='GNU MediaGoblin utilities.')

    subparsers = parser.add_subparsers(help='sub-command help')
    for command_name, command_struct in SUBCOMMAND_MAP.iteritems():
        if command_struct.has_key('help'):
            subparser = subparsers.add_parser(
                command_name, help=command_struct['help'])
        else:
            subparser = subparsers.add_parser(command_name)

        setup_func = util.import_component(command_struct['setup'])
        exec_func = util.import_component(command_struct['func'])

        setup_func(subparser)

        subparser.set_defaults(func=exec_func)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main_cli()
