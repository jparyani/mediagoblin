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
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.common import simple_printer


def theme_parser_setup(subparser):
    theme_subparsers = subparser.add_subparsers(
        dest=u"subcommand",
        help=u'Theme sub-commands')

    # Install command
    install_parser = theme_subparsers.add_parser(
        u'install', help=u'Install a theme to this mediagoblin instance')
    install_parser.add_argument(
        u'themefile', help=u'The theme archive to be installed')

    theme_subparsers.add_parser(
        u'assetlink',
        help=(
            u"Link the currently installed theme's assets "
            u"to the served theme asset directory"))


###########
# Utilities
###########

def link_assets(theme, link_dir, printer=simple_printer):
    """
    Returns a list of string of text telling the user what we did
    which should be printable.
    """
    link_dir = link_dir.rstrip(os.path.sep)
    link_parent_dir = os.path.dirname(link_dir)

    results = []

    if theme is None:
        printer(_("Cannot link theme... no theme set\n"))
        return results

    def _maybe_unlink_link_dir():
        """unlink link directory if it exists"""
        if os.path.lexists(link_dir) \
                and os.path.islink(link_dir):
            os.unlink(link_dir)
            return True

        return results

    if theme.get('assets_dir') is None:
        printer(_("No asset directory for this theme\n"))
        if _maybe_unlink_link_dir():
            printer(
                _("However, old link directory symlink found; removed.\n"))
        return results

    _maybe_unlink_link_dir()

    # make the link directory parent dirs if necessary
    if not os.path.lexists(link_parent_dir):
        os.makedirs(link_parent_dir)

    os.symlink(
        theme['assets_dir'].rstrip(os.path.sep),
        link_dir)
    printer("Linked the theme's asset directory:\n  %s\nto:\n  %s\n" % (
        theme['assets_dir'], link_dir))


def install_theme(install_dir, themefile):
    pass # TODO ;)


#############
# Subcommands
#############

def assetlink_command(args):
    """
    Link the asset directory of the currently installed theme
    """
    global_config, app_config = setup_global_and_app_config(args.conf_file)
    theme_registry, current_theme = register_themes(app_config)
    link_assets(current_theme, app_config['theme_linked_assets_dir'])


def install_command(args):
    """
    Handle the 'install this theme' subcommand
    """
    global_config, app_config = setup_global_and_app_config(args.conf_file)
    install_dir = app_config['theme_install_dir']
    install_theme(install_dir, args.themefile)


SUBCOMMANDS = {
    'assetlink': assetlink_command,
    'install': install_command}


def theme(args):
    SUBCOMMANDS[args.subcommand](args)
