.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.


===========
Quick Start
===========

This is a quick start. It's not comprehensive, but it walks through
writing a basic plugin called "sampleplugin" which logs "I've been
started!" when ``setup_plugin()`` has been called.

.. todo: Rewrite this to be a useful plugin


Step 1: Files and directories
=============================

GNU MediaGoblin plugins are Python projects at heart. As such, you should
use a standard Python project directory tree::

    sampleplugin/
     |- README
     |- LICENSE
     |- setup.py
     |- sampleplugin/
        |- __init__.py


The outer ``sampleplugin`` directory holds all the project files.

The ``README`` should cover what your plugin does, how to install it,
how to configure it, and all the sorts of things a README should
cover.

The ``LICENSE`` should have the license under which you're
distributing your plugin.

The inner ``sampleplugin`` directory is the Python package that holds
your plugin's code.

The ``__init__.py`` denotes that this is a Python package. It also
holds the plugin code and the ``hooks`` dict that specifies which
hooks the sampleplugin uses.


Step 2: README
==============

Here's a rough ``README``. Generally, you want more information
because this is the file that most people open when they want to learn
more about your project.

::

    README
    ======

    This is a sample plugin. It logs a line when ``setup__plugin()`` is
    run.


Step 3: LICENSE
===============

GNU MediaGoblin plugins must be licensed under the AGPLv3 or later. So
the LICENSE file should be the AGPLv3 text which you can find at
`<http://www.gnu.org/licenses/agpl-3.0.html>`_


Step 4: setup.py
================

This file is used for packaging and distributing your plugin.

We'll use a basic one::

    from setuptools import setup, find_packages

    setup(
        name='sampleplugin',
        version='1.0',
        packages=find_packages(),
        include_package_data=True,
        install_requires=[],
        license='AGPLv3',
        )


See `<http://docs.python.org/distutils/index.html#distutils-index>`_
for more details.


Step 5: the code
================

The code for ``__init__.py`` looks like this:

.. code-block:: python
   :linenos:
   :emphasize-lines: 12,23

    import logging
    from mediagoblin.tools.pluginapi import Plugin, get_config


    # This creates a logger that you can use to log information to
    # the console or a log file.
    _log = logging.getLogger(__name__)


    # This is the function that gets called when the setup
    # hook fires.
    def setup_plugin():
        _log.info("I've been started!")
        config = get_config('sampleplugin')
        if config:
            _log.info('%r' % config)
        else:
            _log.info('There is no configuration set.')


    # This is a dict that specifies which hooks this plugin uses.
    # This one only uses one hook: setup.
    hooks = {
        'setup': setup_plugin
        }


Line 12 defines the ``setup_plugin`` function.

Line 23 defines ``hooks``. When MediaGoblin loads this file, it sees
``hooks`` and registers all the callables with their respective hooks.


Step 6: Installation and configuration
======================================

To install the plugin for development, you need to make sure it's
available to the Python interpreter that's running MediaGoblin.

There are a couple of ways to do this, but we're going to pick the
easy one.

Use ``python`` from your MediaGoblin virtual environment and do::

    python setup.py develop

Any changes you make to your plugin will be available in your
MediaGoblin virtual environment.

Then adjust your ``mediagoblin.ini`` file to load the plugin::

    [plugins]

    [[sampleplugin]]


Step 7: That's it!
==================

When you launch MediaGoblin, it'll load the plugin and you'll see
evidence of that in the log file.

That's it for the quick start!


Where to go from here
=====================

See the documentation on the plugin API for code samples and other
things you can use when building your plugin.

See `Hitchhiker's Guide to Packaging
<http://guide.python-distribute.org/>`_ for more information on
packaging your plugin.
