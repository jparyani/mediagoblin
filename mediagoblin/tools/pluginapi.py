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
This module implements the plugin api bits.

Two things about things in this module:

1. they should be excessively well documented because we should pull
   from this file for the docs

2. they should be well tested


How do plugins work?
====================

Plugins are structured like any Python project. You create a Python package.
In that package, you define a high-level ``__init__.py`` module that has a
``hooks`` dict that maps hooks to callables that implement those hooks.

Additionally, you want a LICENSE file that specifies the license and a
``setup.py`` that specifies the metadata for packaging your plugin. A rough
file structure could look like this::

    myplugin/
     |- setup.py         # plugin project packaging metadata
     |- README           # holds plugin project information
     |- LICENSE          # holds license information
     |- myplugin/        # plugin package directory
        |- __init__.py   # has hooks dict and code


Lifecycle
=========

1. All the modules listed as subsections of the ``plugins`` section in
   the config file are imported. MediaGoblin registers any hooks in
   the ``hooks`` dict of those modules.

2. After all plugin modules are imported, the ``setup`` hook is called
   allowing plugins to do any set up they need to do.

"""

import logging

from functools import wraps

from mediagoblin import mg_globals


_log = logging.getLogger(__name__)


class PluginManager(object):
    """Manager for plugin things

    .. Note::

       This is a Borg class--there is one and only one of this class.
    """
    __state = {
        # list of plugin classes
        "plugins": [],

        # map of hook names -> list of callables for that hook
        "hooks": {},

        # list of registered template paths
        "template_paths": set(),

        # list of template hooks
        "template_hooks": {},

        # list of registered routes
        "routes": [],
        }

    def clear(self):
        """This is only useful for testing."""
        # Why lists don't have a clear is not clear.
        del self.plugins[:]
        del self.routes[:]
        self.hooks.clear()
        self.template_paths.clear()

    def __init__(self):
        self.__dict__ = self.__state

    def register_plugin(self, plugin):
        """Registers a plugin class"""
        self.plugins.append(plugin)

    def register_hooks(self, hook_mapping):
        """Takes a hook_mapping and registers all the hooks"""
        for hook, callables in hook_mapping.items():
            if isinstance(callables, (list, tuple)):
                self.hooks.setdefault(hook, []).extend(list(callables))
            else:
                # In this case, it's actually a single callable---not a
                # list of callables.
                self.hooks.setdefault(hook, []).append(callables)

    def get_hook_callables(self, hook_name):
        return self.hooks.get(hook_name, [])

    def register_template_path(self, path):
        """Registers a template path"""
        self.template_paths.add(path)

    def get_template_paths(self):
        """Returns a tuple of registered template paths"""
        return tuple(self.template_paths)

    def register_route(self, route):
        """Registers a single route"""
        _log.debug('registering route: {0}'.format(route))
        self.routes.append(route)

    def get_routes(self):
        return tuple(self.routes)

    def register_template_hooks(self, template_hooks):
        for hook, templates in template_hooks.items():
            if isinstance(templates, (list, tuple)):
                self.template_hooks.setdefault(hook, []).extend(list(templates))
            else:
                # In this case, it's actually a single callable---not a
                # list of callables.
                self.template_hooks.setdefault(hook, []).append(templates)

    def get_template_hooks(self, hook_name):
        return self.template_hooks.get(hook_name, [])


def register_routes(routes):
    """Registers one or more routes

    If your plugin handles requests, then you need to call this with
    the routes your plugin handles.

    A "route" is a `routes.Route` object. See `the routes.Route
    documentation
    <http://routes.readthedocs.org/en/latest/modules/route.html>`_ for
    more details.

    Example passing in a single route:

    >>> register_routes(('about-view', '/about',
    ...     'mediagoblin.views:about_view_handler'))

    Example passing in a list of routes:

    >>> register_routes([
    ...     ('contact-view', '/contact', 'mediagoblin.views:contact_handler'),
    ...     ('about-view', '/about', 'mediagoblin.views:about_handler')
    ... ])


    .. Note::

       Be careful when designing your route urls. If they clash with
       core urls, then it could result in DISASTER!
    """
    if isinstance(routes, list):
        for route in routes:
            PluginManager().register_route(route)
    else:
        PluginManager().register_route(routes)


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
    PluginManager().register_template_path(path)


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


def register_template_hooks(template_hooks):
    """
    Register a dict of template hooks.

    Takes template_hooks as an argument, which is a dictionary of
    template hook names/keys to the templates they should provide.
    (The value can either be a single template path or an iterable
    of paths.)

    Example:

    .. code-block:: python

      {"media_sidebar": "/plugin/sidemess/mess_up_the_side.html",
       "media_descriptionbox": ["/plugin/sidemess/even_more_mess.html",
                                "/plugin/sidemess/so_much_mess.html"]}
    """
    PluginManager().register_template_hooks(template_hooks)


def get_hook_templates(hook_name):
    """
    Get a list of hook templates for this hook_name.

    Note: for the most part, you access this via a template tag, not
    this method directly, like so:

    .. code-block:: html+jinja

      {% template_hook "media_sidebar" %}

    ... which will include all templates for you, partly using this
    method.

    However, this method is exposed to templates, and if you wish, you
    can iterate over templates in a template hook manually like so:

    .. code-block:: html+jinja

      {% for template_path in get_hook_templates("media_sidebar") %}
        <div class="extra_structure">
          {% include template_path %}
        </div>
      {% endfor %}

    Returns:
      A list of strings representing template paths.
    """
    return PluginManager().get_template_hooks(hook_name)


###########################
# Callable convenience code
###########################

class CantHandleIt(Exception):
    """
    A callable may call this method if they look at the relevant
    arguments passed and decide it's not possible for them to handle
    things.
    """
    pass

class UnhandledCallable(Exception):
    """
    Raise this method if no callables were available to handle the
    specified hook.  Only used by callable_runone.
    """
    pass


def callable_runone(hookname, *args, **kwargs):
    """
    Run the callable hook HOOKNAME... run until the first response,
    then return.

    This function will run stop at the first hook that handles the
    result.  Hooks raising CantHandleIt will be skipped.

    Unless unhandled_okay is True, this will error out if no hooks
    have been registered to handle this function.
    """
    callables = PluginManager().get_hook_callables(hookname)

    unhandled_okay = kwargs.pop("unhandled_okay", False)

    for callable in callables:
        try:
            return callable(*args, **kwargs)
        except CantHandleIt:
            continue

    if unhandled_okay is False:
        raise UnhandledCallable(
            "No hooks registered capable of handling '%s'" % hookname)


def callable_runall(hookname, *args, **kwargs):
    """
    Run all callables for HOOKNAME.

    This method will run *all* hooks that handle this method (skipping
    those that raise CantHandleIt), and will return a list of all
    results.
    """
    callables = PluginManager().get_hook_callables(hookname)

    results = []

    for callable in callables:
        try:
            results.append(callable(*args, **kwargs))
        except CantHandleIt:
            continue

    return results
