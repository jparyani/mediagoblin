.. _configuration-chapter:

========================
Configuring MediaGoblin
========================

So!  You've got MediaGoblin up and running, but you need to adjust
some configuration parameters.  Well you've come to the right place!

MediaGoblin's config files
==========================

When configuring MediaGoblin, there are two files you might want to
make local modified versions of, and one extra file that might be
helpful to look at.  Let's examine these.

mediagoblin.ini
  The config file for MediaGoblin, the application.  If you want to
  tweak settings for MediaGoblin, you'll usually tweak them here.

paste.ini
  Primarily a server configuration file, on the python side
  (specifically, on the wsgi side, via `paste deploy
  <http://pythonpaste.org/deploy/>`_ / `paste script
  <http://pythonpaste.org/script/>`_).  It also sets up some
  middleware that you can mostly ignore, except to configure
  sessions... more on that later.  If you are adding a different
  python server other than fastcgi / plain http, you might configure
  it here.  Mostly you won't touch this file as much, probably.


There's one more file that you certainly won't change unless you're
making coding contributions to mediagoblin, but which can be useful to
read and reference:

mediagoblin/config_spec.ini
  This file is actually a specification for mediagoblin.ini itself, as
  a config file!  It defines types and defaults.  Sometimes it's a
  good place to look for documentation... or to find out that hidden
  option that we didn't tell you about. :)


Making local copies
===================


Common changes
==============


Celery
======

We should point to another celery-specific section of the document
actually :)
