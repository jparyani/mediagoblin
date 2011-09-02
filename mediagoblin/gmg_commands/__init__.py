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

import argparse

from mediagoblin import util as mg_util


SUBCOMMAND_MAP = {
    'shell': {
        'setup': 'mediagoblin.gmg_commands.shell:shell_parser_setup',
        'func': 'mediagoblin.gmg_commands.shell:shell',
        'help': 'Run a shell with some tools pre-setup'},
    'migrate': {
        'setup': 'mediagoblin.gmg_commands.migrate:migrate_parser_setup',
        'func': 'mediagoblin.gmg_commands.migrate:migrate',
        'help': 'Apply all unapplied bulk migrations to the database'},
    'adduser':{
        'setup': 'mediagoblin.gmg_commands.users:adduser_parser_setup',
        'func': 'mediagoblin.gmg_commands.users:adduser',
        'help': 'Creates an user'},
    'makeadmin': {
        'setup': 'mediagoblin.gmg_commands.users:makeadmin_parser_setup',
        'func': 'mediagoblin.gmg_commands.users:makeadmin',
        'help': 'Changes a user\'s password'},
    'changepw': {
        'setup': 'mediagoblin.gmg_commands.users:changepw_parser_setup',
        'func': 'mediagoblin.gmg_commands.users:changepw',
        'help': 'Makes admin an user'},
    'wipealldata': {
        'setup': 'mediagoblin.gmg_commands.wipealldata:wipe_parser_setup',
        'func': 'mediagoblin.gmg_commands.wipealldata:wipe',
        'help': 'Wipes **all** the data for this MediaGoblin instance'},
    'env_export': {
        'setup': 'mediagoblin.gmg_commands.import_export:import_export_parse_setup',
        'func': 'mediagoblin.gmg_commands.import_export:env_export',
        'help': 'Exports the data for this MediaGoblin instance'},
    'env_import': {
        'setup': 'mediagoblin.gmg_commands.import_export:import_export_parse_setup',
        'func': 'mediagoblin.gmg_commands.import_export:env_import',
        'help': 'Exports the data for this MediaGoblin instance'},
    }


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

        setup_func = mg_util.import_component(command_struct['setup'])
        exec_func = mg_util.import_component(command_struct['func'])

        setup_func(subparser)

        subparser.set_defaults(func=exec_func)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main_cli()

