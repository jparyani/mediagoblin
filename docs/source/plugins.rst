=========
 Plugins
=========

GNU MediaGoblin supports plugins that, when installed, allow you to
augment MediaGoblin's behavior.

This chapter covers discovering, installing, configuring and removing
plugins.


Discovering plugins
===================

MediaGoblin comes with core plugins. Core plugins are located in the
``mediagoblin.plugins`` module of the MediaGoblin code. Because they
come with MediaGoblin, you don't have to install them, but you do have
to add them to your config file if you're interested in using them.

You can also write your own plugins and additionally find plugins
elsewhere on the Internet. Since these plugins don't come with
MediaGoblin, you must first install them, then add them to your
configuration.


Installing plugins
==================

MediaGoblin core plugins don't need to be installed. For core plugins,
you can skip installation!

If the plugin is not a core plugin and is packaged and available on
the Python Package Index, then you can install the plugin with pip::

    pip install <plugin-name>

For example, if we wanted to install the plugin named
"mediagoblin-restrictfive", we would do::

    pip install mediagoblin-restrictfive

.. Note::

   If you're using a virtual environment, make sure to activate the
   virtual environment before installing with pip. Otherwise the
   plugin may get installed in a different environment.

Once you've installed the plugin software, you need to tell
MediaGoblin that this is a plugin you want MediaGoblin to use. To do
that, you edit the ``mediagoblin.ini`` file and add the plugin as a
subsection of the plugin section.

For example, say the "mediagoblin-restrictfive" plugin had the Python
package path ``restrictfive``, then you would add ``restrictfive`` to
the ``plugins`` section as a subsection::

    [plugins]

    [[restrictfive]]


Configuring plugins
===================

Generally, configuration goes in the ``.ini`` file. Configuration for
a specific plugin, goes in a subsection of the ``plugins`` section.

Example 1: Core MediaGoblin plugin

If you wanted to use the core MediaGoblin flatpages plugin, the module
for that is ``mediagoblin.plugins.flatpages`` and you would add that
to your ``.ini`` file like this::

    [plugins]

    [[mediagoblin.plugins.flatpages]]
    # configuration for flatpages plugin here!

Example 2: Plugin that is not a core MediaGoblin plugin

If you installed a hypothetical restrictfive plugin which is in the
module ``restrictfive``, your ``.ini`` file might look like this (with
comments making the bits clearer)::

    [plugins]

    [[restrictfive]]
    # configuration for restrictfive here!

Check the plugin's documentation for what configuration options are
available.


Removing plugins
================

To remove a plugin, use ``pip uninstall``. For example::

    pip uninstall mediagoblin-restrictfive

.. Note::

   If you're using a virtual environment, make sure to activate the
   virtual environment before uninstalling with pip. Otherwise the
   plugin may get installed in a different environment.
