.. MediaGoblin Documentation

   Written in 2013 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.


==========
Plugin API
==========

This documents the general plugin API.

Please note, at this point OUR PLUGIN HOOKS MAY AND WILL CHANGE.
Authors are encouraged to develop plugins and work with the
MediaGoblin community to keep them up to date, but this API will be a
moving target for a few releases.

Please check the release notes for updates!

:mod:`pluginapi` Module
-----------------------

.. automodule:: mediagoblin.tools.pluginapi
   :members: get_config, register_routes, register_template_path,
             register_template_hooks, get_hook_templates,
             hook_handle, hook_runall, hook_transform
