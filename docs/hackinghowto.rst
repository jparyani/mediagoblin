.. _hacking-howto:

===============
 Hacking HOWTO
===============


So you want to hack on GNU MediaGoblin?
=======================================

First thing to do is check out the Web site where we list all the
project infrastructure including:

* the mailing list
* the IRC channel
* the bug tracker

Additionally, we have information on how to get involved, who to talk
to, what needs to be worked on, and other things besides!


How to set up an environment for hacking
========================================

If running Debian GNU/Linux or a Debian-derived distro such as Mint or
Ubuntu, running the following should install necessary dependencies:

   sudo apt-get install mongodb git-core python python-dev python-lxml

Note: The following instructions describe a development environment
that uses `zc.buildout <http://www.buildout.org/>`_ because it
involves less steps to get things running and less knowledge of python
packaging.  However, if you prefer to use
`virtualenv <http://pypi.python.org/pypi/virtualenv>`_,
that should work just fine.

Follow these steps:

1. clone the repository::

      git clone http://git.gitorious.org/mediagoblin/mediagoblin.git

2. Bootstrap and run buildout::

      cd mediagoblin
      python bootstrap.py && ./bin/buildout

Now whenever you want to update mediagoblin's dependencies, just run::

      ./bin/buildout


Using this method, buildout should create a user_dev directory, in
which certain things will be stored (media, beaker session stuff,
etc).  You can change this, but for development purposes this default
should be fine.


Running the test suite
======================

Run::

      ./bin/nosetests


Creating a new file
===================

FIXME - this needs to be updated when it's set in stone.

All new files need to have license/copyright information.

The following kinds of files get the GNU AGPL header:

* Python files
* JavaScript files
* templates
* other files with code in them

The following files get a CC BY header:

* CSS files

The following files don't get a header because that's hard, but are
under the CC BY license:

* image files
* video files


Quickstart for Django programmers
=================================

FIXME - write this


Bite-sized bugs to start with
=============================

FIXME - write this
