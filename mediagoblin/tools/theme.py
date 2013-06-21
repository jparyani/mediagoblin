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

"""
"""


import pkg_resources
import os

from configobj import ConfigObj


BUILTIN_THEME_DIR = pkg_resources.resource_filename('mediagoblin', 'themes')


def themedata_for_theme_dir(name, theme_dir):
    """
    Given a theme directory, extract important theme information.
    """
    # open config
    config = ConfigObj(os.path.join(theme_dir, 'theme.ini')).get('theme', {})

    templates_dir = os.path.join(theme_dir, 'templates')
    if not os.path.exists(templates_dir):
        templates_dir = None

    assets_dir = os.path.join(theme_dir, 'assets')
    if not os.path.exists(assets_dir):
        assets_dir = None

    themedata = {
        'name': config.get('name', name),
        'description': config.get('description'),
        'licensing': config.get('licensing'),
        'dir': theme_dir,
        'templates_dir': templates_dir,
        'assets_dir': assets_dir,
        'config': config}

    return themedata


def register_themes(app_config, builtin_dir=BUILTIN_THEME_DIR):
    """
    Register all themes relevant to this application.
    """
    registry = {}

    def _install_themes_in_dir(directory):
        for themedir in os.listdir(directory):
            abs_themedir = os.path.join(directory, themedir)
            if not os.path.isdir(abs_themedir):
                continue

            themedata = themedata_for_theme_dir(themedir, abs_themedir)
            registry[themedir] = themedata
        
    # Built-in themes
    if os.path.exists(builtin_dir):
        _install_themes_in_dir(builtin_dir)

    # Installed themes
    theme_install_dir = app_config.get('theme_install_dir')
    if theme_install_dir and os.path.exists(theme_install_dir):
        _install_themes_in_dir(theme_install_dir)

    current_theme_name = app_config.get('theme')
    if current_theme_name \
            and registry.has_key(current_theme_name):
        current_theme = registry[current_theme_name]
    else:
        current_theme = None

    return registry, current_theme

