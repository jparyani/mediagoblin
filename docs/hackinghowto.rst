.. _hacking-howto:

===============
 Hacking HOWTO
===============

.. contents:: Sections
   :local:


So you want to hack on GNU MediaGoblin?
=======================================

First thing to do is check out the `Web site
<http://mediagoblin.org/join/>`_ where we list all the project
infrastructure including:

* the IRC channel
* the mailing list
* the issue tracker

Additionally, we have information on how to get involved, who to talk
to, what needs to be worked on, and other things besides!

Second thing to do is take a look at :ref:`codebase-chapter` where
we've started documenting how GNU MediaGoblin is built and how to add
new things.

Third you'll need to :ref:`get the requirements
<get-requirements-section>`.

Fourth, you'll need to build a development environment.  We use buildout,
but if you want to use virtualenv, there's a set of mediocre not-very-supported
steps in the `wiki <https://gitorious.org/mediagoblin/pages/Home>`_.


.. _get-requirements-section:

Getting requirements
====================

First, you need to have the following installed before you can build
an environment for hacking on GNU MediaGoblin:

* Python 2.6 or 2.7  - http://www.python.org/

  You'll need Python as well as the dev files for building modules.

* python-lxml        - http://lxml.de/
* git                - http://git-scm.com/
* MongoDB            - http://www.mongodb.org/

If you're running Debian GNU/Linux or a Debian-derived distribution
such as Mint or Ubuntu, running the following should install these
requirements::

    sudo apt-get install mongodb git-core python python-dev \
         python-lxml

.. YouCanHelp::

   If you have instructions for other GNU/Linux distributions to set
   up requirements, let us know!


.. _hacking-with-buildout:


How to set up and maintain an environment for hacking with buildout
===================================================================

**Requirements**

No additional requirements.


**Create a development environment**

After installing the requirements, follow these steps:

1. Clone the repository::

       git clone http://git.gitorious.org/mediagoblin/mediagoblin.git

2. Bootstrap and run buildout::

       cd mediagoblin
       python bootstrap.py && ./bin/buildout


That's it!  Using this method, buildout should create a ``user_dev``
directory, in which certain things will be stored (media, beaker
session stuff, etc).  You can change this, but for development
purposes this default should be fine.


**Updating for dependency changes**

While hacking on GNU MediaGoblin over time, you'll eventually have to
update your development environment because the dependencies have
changed.  To do that, run::

    ./bin/buildout && ./bin/gmg migrate


**Updating for code changes**

You don't need to do anything---code changes are automatically
available.


**Deleting your buildout**

At some point, you may want to delete your buildout.  Perhaps it's to
start over.  Perhaps it's to test building development environments
with buildout.

To do this, do::

    rm -rf bin develop-eggs eggs mediagoblin.egg-info parts user_dev


Running the server
==================

If you want to get things running quickly and without hassle, just
run::

    ./lazyserver.sh

This will start up a python server where you can begin playing with
mediagoblin.  It will also run celery in "always eager" mode so you
don't have to start a separate process for it.

This is fine in development, but if you want to actually run celery
separately for testing (or deployment purposes), you'll want to run
the server independently::

    ./bin/paster serve paste.ini --reload


Running celeryd
===============

If you aren't using ./lazyserver.sh or otherwise aren't running celery
in always eager mode, you'll need to do this if you want your media to
process and actually show up.  It's probably a good idea in
development to have the web server (above) running in one terminal and
celeryd in another window.

Run::

    CELERY_CONFIG_MODULE=mediagoblin.init.celery.from_celery ./bin/celeryd


Running the test suite
======================

Run::

    ./runtests.sh


Running a shell
===============

If you want a shell with your database pre-setup and an instantiated
application ready and at your fingertips....

Run::

    ./bin/gmg shell


Troubleshooting
===============

pymongo.errors.AutoReconnect: could not find master/primary
-----------------------------------------------------------

If you see this::

    pymongo.errors.AutoReconnect: could not find master/primary

then make sure mongodb is installed and running.

If it's installed, check the mongodb log.  On my machine, that's 
``/var/log/mongodb/mongodb.log``.  If you see something like::

    old lock file: /var/lib/mongodb/mongod.lock.  probably means...

Then delete the lock file and relaunch mongodb.


Wiping your user data
=====================

.. Note::

   Unless you're doing development and working on and testing creating
   a new instance, you will probably never have to do this.  Will
   plans to do this work and thus he documented it.

.. YouCanHelp::

   If you're familiar with MongoDB, we'd love to get a `script that
   removes all the GNU MediaGoblin data from an existing instance
   <http://bugs.foocorp.net/issues/296>`_.  Let us know!


Quickstart for Django programmers
=================================

We're not using Django, but the codebase is very Django-like in its
structure.

* ``routing.py`` is like ``urls.py`` in Django
* ``models.py`` has mongokit ORM definitions
* ``views.py`` is where the views go

We're using MongoDB.  Basically, instead of a relational database with
tables, you have a big JSON structure which acts a lot like a Python
dict.


.. YouCanHelp::

   If there are other things that you think would help orient someone
   new to GNU MediaGoblin but coming from Django, let us know!


Bite-sized bugs to start with
=============================

**May 3rd, 2011**:  We don't have a list of bite-sized bugs, yet, but
this is important to us.  If you're interested in things to work on,
let us know on `the mailing list <http://mediagoblin.org/join/>`_ or
on the `IRC channel <http://mediagoblin.org/join/>`_.


Tips for people new to coding
=============================

Learning Python
---------------

GNU MediaGoblin is written using a programming language called `Python
<http://python.org/>`_.

There are two different incompatible iterations of Python which I'll
refer to as Python 2 and Python 3.  GNU MediaGoblin is written in
Python 2 and requires Python 2.6 or 2.7.  At some point, we might
switch to Python 3, but that's a future thing.

You can learn how to code in Python 2 from several excellent books
that are freely available on the Internet:

* `Learn Python the Hard Way <http://learnpythonthehardway.org/>`_
* `Dive Into Pyton <http://diveintopython.org/>`_
* `Python for Software Design <http://www.greenteapress.com/thinkpython/>`_
* `A Byte of Python <http://www.swaroopch.com/notes/Python>`_

These are all excellent texts.

.. YouCanHelp::

   If you know of other good quality Python tutorials and Python
   tutorial videos, let us know!


Learning Libraries GNU MediaGoblin uses
---------------------------------------

GNU MediaGoblin uses a variety of libraries in order to do what it
does.  These libraries are listed in the :ref:`codebase-chapter`
along with links to the project Web sites and documentation for the
libraries.

There are a variety of Python-related conferences every year that have
sessions covering many aspects of these libraries.  You can find them
at `Python Miro Community <http://python.mirocommunity.org>`_ [0]_.

.. [0] This is a shameless plug.  Will Kahn-Greene runs Python Miro
   Community.

If you have questions or need help, find us on the mailing list and on
IRC.


.. _hacking-howto-git:

Learning git
------------

git is an interesting and very powerful tool.  Like all powerful
tools, it has a learning curve.

If you're new to git, we highly recommend the following resources for
getting the hang of it:

* `Learn Git <http://learn.github.com/p/intro.html>`_ --- the GitHub
  intro to git
* `Pro Git <http://progit.org/book/>`_ --- fantastic book
* `Git casts <http://gitcasts.com/>`_ --- screencast covering git
  usage
* `Git Reference <http://gitref.org/>`_ --- Git reference that makes
  it easier to get the hang of git if you're coming from other version
  control systems

There's also a git mission at `OpenHatch <http://openhatch.org/>`_.


Learning other utilities
------------------------

The `OpenHatch <http://openhatch.org/>`_ site has a series of
`training missions <http://openhatch.org/missions/>`_ which are
designed to help you learn how to use these tools.

If you're new to tar, diff, patch and git, we highly recommend you sign
up with OpenHatch and do the missions.
