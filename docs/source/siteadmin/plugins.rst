=========
 Plugins
=========

GNU MediaGoblin supports plugins that allow you to augment MediaGoblin's
behavior.

This chapter covers discovering, installing, configuring and removing
plugins.


Discovering plugins
===================

MediaGoblin comes with core plugins. Core plugins are located in the
``mediagoblin.plugins`` module of the MediaGoblin code. Because they
come with MediaGoblin, you don't have to install them, but you do have
to add them to your config file if you're interested in using them.

You can also write your own plugins and additionally find plugins
elsewhere on the Internet. Once you find a plugin you like, you need
to first install it, then add it to your configuration.

.. todo: how do you find plugins on the internet?


Installing plugins
==================

Core plugins
------------

MediaGoblin core plugins don't need to be installed because they come
with MediaGoblin. Further, when you upgrade MediaGoblin, you will also
get updates to the core plugins.


Other plugins
-------------

If the plugin is available on the `Python Package Index
<http://pypi.python.org/pypi>`_, then you can install the plugin with pip::

    pip install <plugin-name>

For example, if we wanted to install the plugin named
"mediagoblin-licenses" (which allows you to customize the licenses you
offer for your media), we would do::

    pip install mediagoblin-licenses

.. Note::

   If you're using a virtual environment, make sure to activate the
   virtual environment before installing with pip. Otherwise the plugin
   may get installed in a different environment than the one MediaGoblin
   is installed in. Also make sure, you use e.g. pip-2.7 if your default
   python (and thus pip) is python 3 (e.g. in Ubuntu).

Once you've installed the plugin software, you need to tell
MediaGoblin that this is a plugin you want MediaGoblin to use. To do
that, you edit the ``mediagoblin.ini`` file and add the plugin as a
subsection of the plugin section.

For example, say the "mediagoblin-licenses" plugin has the Python
package path ``mediagoblin_licenses``, then you would add ``mediagoblin_licenses`` to
the ``plugins`` section as a subsection::

    [plugins]

    [[mediagoblin_licenses]]
    license_01=abbrev1, name1, http://url1
    license_02=abbrev2, name1, http://url2


Configuring plugins
===================

Configuration for a plugin goes in the subsection for that plugin. Core
plugins are documented in the administration guide. Other plugins
should come with documentation that tells you how to configure them.

Example 1: Core MediaGoblin plugin

If you wanted to use the core MediaGoblin flatpages plugin, the module
for that is ``mediagoblin.plugins.flatpagesfile`` and you would add
that to your ``.ini`` file like this::

    [plugins]

    [[mediagoblin.plugins.flatpagesfile]]
    # configuration for flatpagesfile plugin here!
    about-view = '/about', about.html
    terms-view = '/terms', terms.html

(Want to know more about the flatpagesfile plugin?  See
:ref:`flatpagesfile-chapter`)

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

    pip uninstall mediagoblin-licenses

.. Note::

   If you're using a virtual environment, make sure to activate the
   virtual environment before uninstalling with pip. Otherwise the
   plugin may get installed in a different environment.


Upgrading plugins
=================

Core plugins
------------

Core plugins get upgraded automatically when you upgrade MediaGoblin
because they come with MediaGoblin.


Other plugins
-------------

For plugins that you install with pip, you can upgrade them with pip::

    pip install -U <plugin-name>

The ``-U`` tells pip to upgrade the package.


Troubleshooting plugins
=======================

Sometimes plugins just don't work right. When you're having problems
with plugins, think about the following:

1. Check the log files.

   Some plugins will log errors to the log files and you can use that
   to diagnose the problem.

2. Try running MediaGoblin without that plugin.

   It's easy to disable a plugin from MediaGoblin. Add a ``-`` to the
   name in your config file.

   For example, change::

       [[mediagoblin.plugins.flatpagesfile]]

   to::

       [[-mediagoblin.plugins.flatpagesfile]]

   That'll prevent the ``mediagoblin.plugins.flatpagesfile`` plugin from
   loading.

3. If it's a core plugin that comes with MediaGoblin, ask us for help!

   If it's a plugin you got from somewhere else, ask them for help!
