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

import sys

from configobj import ConfigObj
import pytest

from mediagoblin import mg_globals
from mediagoblin.init.plugins import setup_plugins
from mediagoblin.tools import pluginapi


def with_cleanup(*modules_to_delete):
    def _with_cleanup(fun):
        """Wrapper that saves and restores mg_globals"""
        def _with_cleanup_inner(*args, **kwargs):
            old_app_config = mg_globals.app_config
            old_global_config = mg_globals.global_config
            # Need to delete icky modules before and after so as to make
            # sure things work correctly.
            for module in modules_to_delete:
                try:
                    del sys.modules[module]
                except KeyError:
                    pass
            # The plugin cache gets populated as a side-effect of
            # importing, so it's best to clear it before and after a test.
            pman = pluginapi.PluginManager()
            pman.clear()
            try:
                return fun(*args, **kwargs)
            finally:
                mg_globals.app_config = old_app_config
                mg_globals.global_config = old_global_config
                # Need to delete icky modules before and after so as to make
                # sure things work correctly.
                for module in modules_to_delete:
                    try:
                        del sys.modules[module]
                    except KeyError:
                        pass
                pman.clear()

        _with_cleanup_inner.__name__ = fun.__name__
        return _with_cleanup_inner
    return _with_cleanup


def build_config(sections):
    """Builds a ConfigObj object with specified data

    :arg sections: list of ``(section_name, section_data,
        subsection_list)`` tuples where section_data is a dict and
        subsection_list is a list of ``(section_name, section_data,
        subsection_list)``, ...

    For example:

    >>> build_config([
    ...    ('mediagoblin', {'key1': 'val1'}, []),
    ...    ('section2', {}, [
    ...        ('subsection1', {}, [])
    ...        ])
    ...    ])
    """
    cfg = ConfigObj()
    cfg.filename = 'foo'
    def _iter_section(cfg, section_list):
        for section_name, data, subsection_list in section_list:
            cfg[section_name] = data
            _iter_section(cfg[section_name], subsection_list)

    _iter_section(cfg, sections)
    return cfg


@with_cleanup()
def test_no_plugins():
    """Run setup_plugins with no plugins in config"""
    cfg = build_config([('mediagoblin', {}, [])])
    mg_globals.app_config = cfg['mediagoblin']
    mg_globals.global_config = cfg

    pman = pluginapi.PluginManager()
    setup_plugins()

    # Make sure we didn't load anything.
    assert len(pman.plugins) == 0


@with_cleanup('mediagoblin.plugins.sampleplugin')
def test_one_plugin():
    """Run setup_plugins with a single working plugin"""
    cfg = build_config([
            ('mediagoblin', {}, []),
            ('plugins', {}, [
                    ('mediagoblin.plugins.sampleplugin', {}, [])
                    ])
            ])

    mg_globals.app_config = cfg['mediagoblin']
    mg_globals.global_config = cfg

    pman = pluginapi.PluginManager()
    setup_plugins()

    # Make sure we only found one plugin
    assert len(pman.plugins) == 1
    # Make sure the plugin is the one we think it is.
    assert pman.plugins[0] == 'mediagoblin.plugins.sampleplugin'
    # Make sure there was one hook registered
    assert len(pman.hooks) == 1
    # Make sure _setup_plugin_called was called once
    import mediagoblin.plugins.sampleplugin
    assert mediagoblin.plugins.sampleplugin._setup_plugin_called == 1


@with_cleanup('mediagoblin.plugins.sampleplugin')
def test_same_plugin_twice():
    """Run setup_plugins with a single working plugin twice"""
    cfg = build_config([
            ('mediagoblin', {}, []),
            ('plugins', {}, [
                    ('mediagoblin.plugins.sampleplugin', {}, []),
                    ('mediagoblin.plugins.sampleplugin', {}, []),
                    ])
            ])

    mg_globals.app_config = cfg['mediagoblin']
    mg_globals.global_config = cfg

    pman = pluginapi.PluginManager()
    setup_plugins()

    # Make sure we only found one plugin
    assert len(pman.plugins) == 1
    # Make sure the plugin is the one we think it is.
    assert pman.plugins[0] == 'mediagoblin.plugins.sampleplugin'
    # Make sure there was one hook registered
    assert len(pman.hooks) == 1
    # Make sure _setup_plugin_called was called once
    import mediagoblin.plugins.sampleplugin
    assert mediagoblin.plugins.sampleplugin._setup_plugin_called == 1


@with_cleanup()
def test_disabled_plugin():
    """Run setup_plugins with a single working plugin twice"""
    cfg = build_config([
            ('mediagoblin', {}, []),
            ('plugins', {}, [
                    ('-mediagoblin.plugins.sampleplugin', {}, []),
                    ])
            ])

    mg_globals.app_config = cfg['mediagoblin']
    mg_globals.global_config = cfg

    pman = pluginapi.PluginManager()
    setup_plugins()

    # Make sure we didn't load the plugin
    assert len(pman.plugins) == 0


CONFIG_ALL_CALLABLES = [
        ('mediagoblin', {}, []),
        ('plugins', {}, [
                ('mediagoblin.tests.testplugins.callables1', {}, []),
                ('mediagoblin.tests.testplugins.callables2', {}, []),
                ('mediagoblin.tests.testplugins.callables3', {}, []),
            ])
    ]


@with_cleanup()
def test_hook_handle():
    """
    Test the hook_handle method
    """
    cfg = build_config(CONFIG_ALL_CALLABLES)

    mg_globals.app_config = cfg['mediagoblin']
    mg_globals.global_config = cfg

    setup_plugins()

    # Just one hook provided
    call_log = []
    assert pluginapi.hook_handle(
        "just_one", call_log) == "Called just once"
    assert call_log == ["expect this one call"]

    # Nothing provided and unhandled not okay
    call_log = []
    pluginapi.hook_handle(
        "nothing_handling", call_log) == None
    assert call_log == []

    # Nothing provided and unhandled okay
    call_log = []
    assert pluginapi.hook_handle(
        "nothing_handling", call_log, unhandled_okay=True) is None
    assert call_log == []
    
    # Multiple provided, go with the first!
    call_log = []
    assert pluginapi.hook_handle(
        "multi_handle", call_log) == "the first returns"
    assert call_log == ["Hi, I'm the first"]

    # Multiple provided, one has CantHandleIt
    call_log = []
    assert pluginapi.hook_handle(
        "multi_handle_with_canthandle",
        call_log) == "the second returns"
    assert call_log == ["Hi, I'm the second"]


@with_cleanup()
def test_hook_runall():
    """
    Test the hook_runall method
    """
    cfg = build_config(CONFIG_ALL_CALLABLES)

    mg_globals.app_config = cfg['mediagoblin']
    mg_globals.global_config = cfg

    setup_plugins()

    # Just one hook, check results
    call_log = []
    assert pluginapi.hook_runall(
        "just_one", call_log) == ["Called just once"]
    assert call_log == ["expect this one call"]

    # None provided, check results
    call_log = []
    assert pluginapi.hook_runall(
        "nothing_handling", call_log) == []
    assert call_log == []

    # Multiple provided, check results
    call_log = []
    assert pluginapi.hook_runall(
        "multi_handle", call_log) == [
            "the first returns",
            "the second returns",
            "the third returns",
        ]
    assert call_log == [
        "Hi, I'm the first",
        "Hi, I'm the second",
        "Hi, I'm the third"]

    # Multiple provided, one has CantHandleIt, check results
    call_log = []
    assert pluginapi.hook_runall(
        "multi_handle_with_canthandle", call_log) == [
            "the second returns",
            "the third returns",
        ]
    assert call_log == [
        "Hi, I'm the second",
        "Hi, I'm the third"]


@with_cleanup()
def test_hook_transform():
    """
    Test the hook_transform method
    """
    cfg = build_config(CONFIG_ALL_CALLABLES)

    mg_globals.app_config = cfg['mediagoblin']
    mg_globals.global_config = cfg

    setup_plugins()

    assert pluginapi.hook_transform(
        "expand_tuple", (-1, 0)) == (-1, 0, 1, 2, 3)
