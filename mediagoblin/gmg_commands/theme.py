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

import os

from mediagoblin.init import setup_global_and_app_config
from mediagoblin.tools.theme import register_themes


def theme_parser_setup(subparser):
    theme_subparsers = subparser.add_subparsers(
        dest=u"subcommand",
        help=u'Theme sub-commands')

    # Install command
    install_parser = theme_subparsers.add_parser(
        u'install', help=u'Install a theme to this mediagoblin instance')
    install_parser.add_argument(
        u'themefile', help=u'The theme archive to be installed')

    # # Uninstall command
    # theme_subparsers.add_parser(
    #     u'uninstall',
    #     help=u'Uninstall a theme... will default to the current theme.')

    # # List command
    # theme_subparsers.add_parser(
    #     u'list', help=u'List installed themes')
    
    # Set theme command

    # Link theme assets command

    theme_subparsers.add_parser(
        u'assetlink',
        help=(
            u"Link the currently installed theme's assets "
            u"to the served theme asset directory"))


def assetlink(args):
    """
    Link the asset directory of the currently installed theme
    """
    global_config, app_config = setup_global_and_app_config(args.conf_file)
    theme_registry, current_theme = register_themes(app_config)
    link_dir = app_config['theme_linked_assets_dir'].rstrip(os.path.sep)
    link_parent_dir = os.path.split(link_dir.rstrip(os.path.sep))[0]

    if current_theme is None:
        print "Cannot link theme... no theme set"
        return

    def _maybe_unlink_link_dir():
        """unlink link directory if it exists"""
        if os.path.lexists(link_dir) \
                and os.path.islink(link_dir):
            os.unlink(link_dir)
            return True

        return False

    if current_theme.get('assets_dir') is None:
        print "No asset directory for this theme"
        if _maybe_unlink_link_dir():
            print "However, old link directory symlink found; removed."
        return

    _maybe_unlink_link_dir()

    # make the link directory parent dirs if necessary
    if not os.path.lexists(link_parent_dir):
        os.makedirs(link_parent_dir)

    os.symlink(
        current_theme['assets_dir'].rstrip(os.path.sep),
        link_dir)
    print "Linked the theme's asset directory:\n  %s\nto:\n  %s" % (
        current_theme['assets_dir'], link_dir)


SUBCOMMANDS = {
    'assetlink': assetlink}


def theme(args):
    SUBCOMMANDS[args.subcommand](args)
