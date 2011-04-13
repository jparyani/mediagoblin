===============
 Hacking HOWTO
===============

So you want to hack on GNU MediaGoblin
======================================

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

All new files need to have the standard GNU MediaGoblin
license/copyright header.

For Python files, include the license/copyright header at the top such
that each line of the header starts with ``#``.

For Jinja2 template files, FIXME.

For JavaScript files, FIXME.

For CSS files, FIXME.

If you're doing the copy-paste thing, make sure to update the
copyright year.
