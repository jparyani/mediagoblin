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

from mediagoblin import mg_globals
from mediagoblin.init import setup_global_and_app_config
from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.tools.theme import register_themes
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.common import simple_printer
from mediagoblin.tools import pluginapi


def assetlink_parser_setup(subparser):
    # theme_subparsers = subparser.add_subparsers(
    #     dest=u"subcommand",
    #     help=u'Assetlink options')

    # # Install command
    # install_parser = theme_subparsers.add_parser(
    #     u'install', help=u'Install a theme to this mediagoblin instance')
    # install_parser.add_argument(
    #     u'themefile', help=u'The theme archive to be installed')

    # theme_subparsers.add_parser(
    #     u'assetlink',
    #     help=(
    #         u"Link the currently installed theme's assets "
    #         u"to the served theme asset directory"))
    pass


###########
# Utilities
###########

def link_theme_assets(theme, link_dir, printer=simple_printer):
    """
    Returns a list of string of text telling the user what we did
    which should be printable.
    """
    link_dir = link_dir.rstrip(os.path.sep)
    link_parent_dir = os.path.dirname(link_dir)

    if theme is None:
        printer(_("Cannot link theme... no theme set\n"))
        return

    def _maybe_unlink_link_dir():
        """unlink link directory if it exists"""
        if os.path.lexists(link_dir) \
                and os.path.islink(link_dir):
            os.unlink(link_dir)
            return True

        return

    if theme.get('assets_dir') is None:
        printer(_("No asset directory for this theme\n"))
        if _maybe_unlink_link_dir():
            printer(
                _("However, old link directory symlink found; removed.\n"))
        return

    _maybe_unlink_link_dir()

    # make the link directory parent dirs if necessary
    if not os.path.lexists(link_parent_dir):
        os.makedirs(link_parent_dir)

    os.symlink(
        theme['assets_dir'].rstrip(os.path.sep),
        link_dir)
    printer("Linked the theme's asset directory:\n  %s\nto:\n  %s\n" % (
        theme['assets_dir'], link_dir))


def link_plugin_assets(plugin_static, plugins_link_dir, printer=simple_printer):
    """
    Arguments:
     - plugin_static: a mediagoblin.tools.staticdirect.PluginStatic instance
       representing the static assets of this plugins' configuration
     - plugins_link_dir: Base directory plugins are linked from
    """
    # link_dir is the final directory we'll link to, a combination of
    # the plugin assetlink directory and plugin_static.name
    link_dir = os.path.join(
        plugins_link_dir.rstrip(os.path.sep), plugin_static.name)

    # make the link directory parent dirs if necessary
    if not os.path.lexists(plugins_link_dir):
        os.makedirs(plugins_link_dir)

    # See if the link_dir already exists.
    if os.path.lexists(link_dir):
        # if this isn't a symlink, there's something wrong... error out.
        if not os.path.islink(link_dir):
            printer(_('Could not link "%s": %s exists and is not a symlink\n') % (
                plugin_static.name, link_dir))
            return

        # if this is a symlink and the path already exists, skip it.
        if os.path.realpath(link_dir) == plugin_static.file_path:
            # Is this comment helpful or not?
            printer(_('Skipping "%s"; already set up.\n') % (
                plugin_static.name))
            return

        # Otherwise, it's a link that went to something else... unlink it
        printer(_('Old link found for "%s"; removing.\n') % (
            plugin_static.name))
        os.unlink(link_dir)

    os.symlink(
        plugin_static.file_path.rstrip(os.path.sep),
        link_dir)
    printer('Linked asset directory for plugin "%s":\n  %s\nto:\n  %s\n' % (
        plugin_static.name,
        plugin_static.file_path.rstrip(os.path.sep),
        link_dir))


def assetlink(args):
    """
    Link the asset directory of the currently installed theme and plugins
    """
    mgoblin_app = commands_util.setup_app(args)
    app_config = mg_globals.app_config

    # link theme
    link_theme_assets(mgoblin_app.current_theme, app_config['theme_linked_assets_dir'])

    # link plugin assets
    ## ... probably for this we need the whole application initialized
    for plugin_static in pluginapi.hook_runall("static_setup"):
        link_plugin_assets(
            plugin_static, app_config['plugin_linked_assets_dir'])
