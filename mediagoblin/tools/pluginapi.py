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
This module implements the plugin api bits and provides the plugin
base.

Two things about things in this module:

1. they should be excessively well documented because we should pull
   from this file for the docs

2. they should be well tested


How do plugins work?
====================

Plugins are structured like any Python project. You create a Python package.
In that package, you define a high-level ``__init__.py`` that either defines
or imports modules that define classes that inherit from the ``Plugin`` class.

Additionally, you want a LICENSE file that specifies the license and a
``setup.py`` that specifies the metadata for packaging your plugin. A rough
file structure could look like this::

    myplugin/
     |- setup.py         # plugin project packaging metadata
     |- README           # holds plugin project information
     |- LICENSE          # holds license information
     |- myplugin/        # plugin package directory
        |- __init__.py   # imports myplugin.main
        |- main.py       # code for plugin


Lifecycle
=========

1. All the modules listed as subsections of the ``plugins`` section in
   the config file are imported. This causes any ``Plugin`` subclasses in
   those modules to be defined and when the classes are defined they get
   automatically registered with the ``PluginCache``.

2. After all plugin modules are imported, registered plugin classes are
   instantiated and ``setup_plugin`` is called for each plugin object.

   Plugins can do any setup they need to do in their ``setup_plugin``
   method.
"""

import logging

from mediagoblin import mg_globals


_log = logging.getLogger(__name__)


class PluginCache(object):
    """Cache of plugin things"""
    __state = {
        # list of plugin classes
        "plugin_classes": [],

        # list of plugin objects
        "plugin_objects": [],

        # list of registered template paths
        "template_paths": set(),
        }

    def clear(self):
        """This is only useful for testing."""
        del self.plugin_classes[:]
        del self.plugin_objects[:]

    def __init__(self):
        self.__dict__ = self.__state

    def register_plugin_class(self, plugin_class):
        """Registers a plugin class"""
        self.plugin_classes.append(plugin_class)

    def register_plugin_object(self, plugin_obj):
        """Registers a plugin object"""
        self.plugin_objects.append(plugin_obj)

    def register_template_path(self, path):
        """Registers a template path"""
        self.template_paths.add(path)

    def get_template_paths(self):
        """Returns a tuple of registered template paths"""
        return tuple(self.template_paths)


class MetaPluginClass(type):
    """Metaclass for PluginBase derivatives"""
    def __new__(cls, name, bases, attrs):
        new_class = super(MetaPluginClass, cls).__new__(cls, name, bases, attrs)
        parents = [b for b in bases if isinstance(b, MetaPluginClass)]
        if not parents:
            return new_class
        PluginCache().register_plugin_class(new_class)
        return new_class


class Plugin(object):
    """Exttend this class for plugins.

    Example::

        from mediagoblin.tools.pluginapi import Plugin

        class MyPlugin(Plugin):
            ...

            def setup_plugin(self):
                ....

    """

    __metaclass__ = MetaPluginClass

    def setup_plugin(self):
        pass


def register_template_path(path):
    """Registers a path for template loading

    If your plugin has templates, then you need to call this with
    the absolute path of the root of templates directory.

    Example:

    >>> my_plugin_dir = os.path.dirname(__file__)
    >>> template_dir = os.path.join(my_plugin_dir, 'templates')
    >>> register_template_path(template_dir)

    .. Note::

       You can only do this in `setup_plugins()`. Doing this after
       that will have no effect on template loading.

    """
    PluginCache().register_template_path(path)


def get_config(key):
    """Retrieves the configuration for a specified plugin by key

    Example:

    >>> get_config('mediagoblin.plugins.sampleplugin')
    {'foo': 'bar'}
    >>> get_config('myplugin')
    {}
    >>> get_config('flatpages')
    {'directory': '/srv/mediagoblin/pages', 'nesting': 1}}

    """

    global_config = mg_globals.global_config
    plugin_section = global_config.get('plugins', {})
    return plugin_section.get(key, {})
