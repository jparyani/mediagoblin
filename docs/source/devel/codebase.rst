.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _codebase-chapter:

========================
 Codebase Documentation
========================

.. contents:: Sections
   :local:


This chapter covers the libraries that GNU MediaGoblin uses as well as
various recipes for getting things done.

.. Note::

   This chapter is in flux.  Clearly there are things here that aren't
   documented.  If there's something you have questions about, please
   ask!

   See `the join page on the website <http://mediagoblin.org/join/>`_
   for where we hang out.

For more information on how to get started hacking on GNU MediaGoblin,
see `the wiki <http://wiki.mediagoblin.org/>`_, and specifically, go
through the
`Hacking HOWTO <http://wiki.mediagoblin.org/HackingHowto>`_
which explains generally how to get going with running an instance for
development.


Software Stack
==============

* Project infrastructure

  * `Python <http://python.org/>`_: the language we're using to write
    this

  * `Nose <http://somethingaboutorange.com/mrl/projects/nose/>`_:
    for unit tests

  * `virtualenv <http://www.virtualenv.org/>`_: for setting up an
    isolated environment to keep mediagoblin and related packages
    (potentially not required if MediaGoblin is packaged for your
    distro)

* Data storage

  * `SQLAlchemy <http://sqlalchemy.org/>`_: SQL ORM and database
    interaction library for Python. Currently we support sqlite and
    postgress as backends.

* Web application

  * `Paste Deploy <http://pythonpaste.org/deploy/>`_ and
    `Paste Script <http://pythonpaste.org/script/>`_: we'll use this for
    configuring and launching the application

  * `werkzeug <http://werkzeug.pocoo.org/>`_: nice abstraction layer
    from HTTP requests, responses and WSGI bits

  * `Beaker <http://beaker.groovie.org/>`_: for handling sessions and
    caching

  * `Jinja2 <http://jinja.pocoo.org/docs/>`_: the templating engine

  * `WTForms <http://wtforms.simplecodes.com/>`_: for handling,
    validation, and abstraction from HTML forms

  * `Celery <http://celeryproject.org/>`_: for task queuing (resizing
    images, encoding video, ...)

  * `Babel <http://babel.edgewall.org>`_: Used to extract and compile
    translations.

  * `Markdown (for python) <http://pypi.python.org/pypi/Markdown>`_:
    implementation of `Markdown <http://daringfireball.net/projects/markdown/>`_
    text-to-html tool to make it easy for people to write richtext
    comments, descriptions, and etc.

  * `lxml <http://lxml.de/>`_: nice xml and html processing for
    python.

* Media processing libraries

  * `Python Imaging Library <http://www.pythonware.com/products/pil/>`_:
    used to resize and otherwise convert images for display.

  * `GStreamer <http://gstreamer.freedesktop.org/>`_: (Optional, for
    video hosting sites only) Used to transcode video, and in the
    future, probably audio too.

  * `chardet <http://pypi.python.org/pypi/chardet>`_: (Optional, for
    ascii art hosting sites only)  Used to make ascii art thumbnails.

* Front end

  * `JQuery <http://jquery.com/>`_: for groovy JavaScript things



What's where
============

After you've run checked out mediagoblin and followed the virtualenv
instantiation instructions, you're faced with the following directory
tree::

    mediagoblin/
    |- mediagoblin/              # source code
    |  |- db/                    # database setup
    |  |- tools/                 # various utilities
    |  |- init/                  # "initialization" tools (arguably should be in tools/)
    |  |- tests/                 # unit tests
    |  |- templates/             # templates for this application
    |  |- media_types/           # code for processing, displaying different media
    |  |- storage/               # different storage backends
    |  |- gmg_commands/          # command line tools (./bin/gmg)
    |  |- themes/                # pre-bundled themes
    |  |
    |  |  # ... some submodules here as well for different sections
    |  |  # of the application... here's just a few
    |  |- auth/                  # authentication (login/registration) code
    |  |- user_dev/              # user pages (under /u/), including media pages
    |  \- submit/                # submitting media for processing
    |
    |- docs/                     # documentation
    |- devtools/                 # some scripts for developer convenience
    |
    |- user_dev/                 # local instance sessions, media, etc
    |
    |  # the below directories are installed into your virtualenv checkout
    |
    |- bin/                      # scripts
    |- develop-eggs/
    |- lib/                      # python libraries installed into your virtualenv
    |- include/
    |- mediagoblin.egg-info/
    \- parts/


As you can see, all the code for GNU MediaGoblin is in the
``mediagoblin`` directory.

Here are some interesting files and what they do:

:routing.py: maps url paths to views
:views.py:   views handle http requests
:forms.py:   wtforms stuff for this submodule

You'll notice that there are several sub-directories: tests,
templates, auth, submit, ...

``tests`` holds the unit test code.

``templates`` holds all the templates for the output.

``auth`` and ``submit`` are modules that enacpsulate authentication
and media item submission.  If you look in these directories, you'll
see they have their own ``routing.py``, ``view.py``, and forms.py in
addition to some other code.

You'll also notice that mediagoblin/db/ contains quite a few things,
including the following:

:models.py:      This is where the database is set up
:mixin.py:       Certain functions appended to models from here
:migrations.py:  When creating a new migration (a change to the
                 database structure), we put it here

