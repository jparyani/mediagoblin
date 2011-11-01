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
  This is the config file for MediaGoblin, the application.  If you want to
  tweak settings for MediaGoblin, you'll usually tweak them here.

paste.ini
  This is primarily a server configuration file, on the python side
  (specifically, on the wsgi side, via `paste deploy
  <http://pythonpaste.org/deploy/>`_ / `paste script
  <http://pythonpaste.org/script/>`_).  It also sets up some
  middleware that you can mostly ignore, except to configure
  sessions... more on that later.  If you are adding a different
  python server other than fastcgi / plain http, you might configure
  it here.  You probably won't need to change this file very much.


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

Assuming you're doing the virtualenv setup described elsewhere in this
manual and you need to make local tweaks to the config files, there's
an easy way to do that.

To make changes to mediagoblin.ini:

  cp mediagoblin.ini mediagoblin_local.ini

To make changes to paste.ini:
  cp paste.ini paste_local.ini

From here you should be able to make direct adjustments to the files,
and most of the commands described elsewhere in this manual will "notice"
your local config files and use those instead of the non-local version.

(Note that all commands provide a way to pass in a specific config
file also, usually by a -cf flag.)

Common changes
==============

Enabling email notifications
----------------------------

You'll almost certainly want to enable sending emails.  By default,
MediaGoblin doesn't really do this... for the sake of developer
convenience, it runs in "email debug mode".  Change this:

  email_debug_mode = false

You can (and should) change the "from" email address by setting
``email_sender_address``.

Note that you need a mailer daemon running for this to work.

If you have more custom SMTP settings, you also have the following
options at your disposal, which are all optional, and do exactly what
they sound like.

 - email_smtp_host
 - email_smtp_port
 - email_smtp_user
 - email_smtp_pass

Celery
======

We should point to another celery-specific section of the document
actually :)
