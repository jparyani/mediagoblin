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

import argparse
import os

from mediagoblin.tools.common import import_component


SUBCOMMAND_MAP = {
    'shell': {
        'setup': 'mediagoblin.gmg_commands.shell:shell_parser_setup',
        'func': 'mediagoblin.gmg_commands.shell:shell',
        'help': 'Run a shell with some tools pre-setup'},
    'adduser': {
        'setup': 'mediagoblin.gmg_commands.users:adduser_parser_setup',
        'func': 'mediagoblin.gmg_commands.users:adduser',
        'help': 'Creates an user'},
    'makeadmin': {
        'setup': 'mediagoblin.gmg_commands.users:makeadmin_parser_setup',
        'func': 'mediagoblin.gmg_commands.users:makeadmin',
        'help': 'Makes user an admin'},
    'changepw': {
        'setup': 'mediagoblin.gmg_commands.users:changepw_parser_setup',
        'func': 'mediagoblin.gmg_commands.users:changepw',
        'help': 'Changes a user\'s password'},
    'dbupdate': {
        'setup': 'mediagoblin.gmg_commands.dbupdate:dbupdate_parse_setup',
        'func': 'mediagoblin.gmg_commands.dbupdate:dbupdate',
        'help': 'Set up or update the SQL database'},
    'assetlink': {
        'setup': 'mediagoblin.gmg_commands.assetlink:assetlink_parser_setup',
        'func': 'mediagoblin.gmg_commands.assetlink:assetlink',
        'help': 'Link assets for themes and plugins for static serving'},
    'reprocess': {
        'setup': 'mediagoblin.gmg_commands.reprocess:reprocess_parser_setup',
        'func': 'mediagoblin.gmg_commands.reprocess:reprocess',
        'help': 'Reprocess media entries'},
    'addmedia': {
        'setup': 'mediagoblin.gmg_commands.addmedia:parser_setup',
        'func': 'mediagoblin.gmg_commands.addmedia:addmedia',
        'help': 'Reprocess media entries'},
    'deletemedia': {
        'setup': 'mediagoblin.gmg_commands.deletemedia:parser_setup',
        'func': 'mediagoblin.gmg_commands.deletemedia:deletemedia',
        'help': 'Delete media entries'},
    # 'theme': {
    #     'setup': 'mediagoblin.gmg_commands.theme:theme_parser_setup',
    #     'func': 'mediagoblin.gmg_commands.theme:theme',
    #     'help': 'Theming commands',
    #     }

    ## These might be useful, mayyyybe, but don't really work anymore
    ## due to mongo change and the "versatility" of sql options.
    ##
    ## For now, commenting out.  Might re-enable soonish?
    #
    # 'env_export': {
    #     'setup': 'mediagoblin.gmg_commands.import_export:import_export_parse_setup',
    #     'func': 'mediagoblin.gmg_commands.import_export:env_export',
    #     'help': 'Exports the data for this MediaGoblin instance'},
    # 'env_import': {
    #     'setup': 'mediagoblin.gmg_commands.import_export:import_export_parse_setup',
    #     'func': 'mediagoblin.gmg_commands.import_export:env_import',
    #     'help': 'Imports the data for this MediaGoblin instance'},
    }


def main_cli():
    parser = argparse.ArgumentParser(
        description='GNU MediaGoblin utilities.')
    parser.add_argument(
        '-cf', '--conf_file', default=None,
        help=(
            "Config file used to set up environment.  "
            "Default to mediagoblin_local.ini if readable, "
            "otherwise mediagoblin.ini"))

    subparsers = parser.add_subparsers(help='sub-command help')
    for command_name, command_struct in SUBCOMMAND_MAP.iteritems():
        if 'help' in command_struct:
            subparser = subparsers.add_parser(
                command_name, help=command_struct['help'])
        else:
            subparser = subparsers.add_parser(command_name)

        setup_func = import_component(command_struct['setup'])
        exec_func = import_component(command_struct['func'])

        setup_func(subparser)

        subparser.set_defaults(func=exec_func)

    args = parser.parse_args()
    args.orig_conf_file = args.conf_file
    if args.conf_file is None:
        if os.path.exists('mediagoblin_local.ini') \
                and os.access('mediagoblin_local.ini', os.R_OK):
            args.conf_file = 'mediagoblin_local.ini'
        else:
            args.conf_file = 'mediagoblin.ini'

    args.func(args)


if __name__ == '__main__':
    main_cli()
