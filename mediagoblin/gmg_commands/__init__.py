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
import shutil

import six

from mediagoblin.tools.common import import_component

import logging
_log = logging.getLogger(__name__)
logging.basicConfig()


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
    'deleteuser': {
        'setup': 'mediagoblin.gmg_commands.users:deleteuser_parser_setup',
        'func': 'mediagoblin.gmg_commands.users:deleteuser',
        'help': 'Deletes a user'},
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
    'serve': {
            'setup': 'mediagoblin.gmg_commands.serve:parser_setup',
            'func': 'mediagoblin.gmg_commands.serve:serve',
            'help': 'PasteScript replacement'},
    'batchaddmedia': {
        'setup': 'mediagoblin.gmg_commands.batchaddmedia:parser_setup',
        'func': 'mediagoblin.gmg_commands.batchaddmedia:batchaddmedia',
        'help': 'Add many media entries at once'},
    # 'theme': {
    #     'setup': 'mediagoblin.gmg_commands.theme:theme_parser_setup',
    #     'func': 'mediagoblin.gmg_commands.theme:theme',
    #     'help': 'Theming commands',
    #     }
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
    for command_name, command_struct in six.iteritems(SUBCOMMAND_MAP):
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

    # This is a hopefully TEMPORARY hack for adding a mediagoblin.ini
    # if none exists, to make up for a deficiency as we are migrating
    # our docs to the new "no mediagoblin.ini by default" workflow.
    # Normally, the docs should provide instructions for this, but
    # since 0.7.1 docs say "install from master!" and yet we removed
    # mediagoblin.ini, we need to cover our bases...

    parent_directory = os.path.split(os.path.abspath(args.conf_file))[0]
    if os.path.split(args.conf_file)[1] == 'mediagoblin.ini' \
       and not os.path.exists(args.conf_file) \
       and os.path.exists(
           os.path.join(
               parent_directory, 'mediagoblin.example.ini')):
        # Do the copy-over of the mediagoblin config for the user
        _log.warning(
            "No mediagoblin.ini found and no other path given, "
            "so making one for you.")
        shutil.copy(
            os.path.join(parent_directory, "mediagoblin.example.ini"),
            os.path.join(parent_directory, "mediagoblin.ini"))

    args.func(args)


if __name__ == '__main__':
    main_cli()
