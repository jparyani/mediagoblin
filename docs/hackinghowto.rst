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

The following assumes you have these things installed:

1. virtualenv:

   http://pypi.python.org/pypi/virtualenv

2. virtualenv wrapper: 

   http://www.doughellmann.com/projects/virtualenvwrapper/

3. git:

   http://git-scm.com/


Follow these steps:

1. clone the repository::

      git clone http://git.gitorious.org/mediagoblin/mediagoblin.git

2. create a virtual environment::

      mkvirtualenv mediagoblin

3. if that doesn't put you in the virtual environment you created,
   then do::

      workon mediagoblin

4. run::

      python setup.py develop


When you want to work on GNU MediaGoblin, make sure to enter your
virtual environment::

    workon mediagoblin

Any changes you make to the code will show up in your virtual
environment--there's no need to continuously run ``python setup.py
develop``.


Running the test suite
======================

Run::

    python setup.py test


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
