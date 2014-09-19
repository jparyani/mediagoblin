.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

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
  This is primarily a server configuration file, on the Python side
  (specifically, on the WSGI side, via `paste deploy
  <http://pythonpaste.org/deploy/>`_ / `paste script
  <http://pythonpaste.org/script/>`_).  It also sets up some
  middleware that you can mostly ignore, except to configure
  sessions... more on that later.  If you are adding a different
  Python server other than fastcgi / plain HTTP, you might configure
  it here.  You probably won't need to change this file very much.


There's one more file that you certainly won't change unless you're
making coding contributions to mediagoblin, but which can be useful to
read and reference:

mediagoblin/config_spec.ini
  This file is actually a specification for mediagoblin.ini itself, as
  a config file!  It defines types and defaults.  Sometimes it's a
  good place to look for documentation... or to find that hidden
  option that we didn't tell you about. :)


Making local copies
===================

Let's assume you're doing the virtualenv setup described elsewhere in this
manual, and you need to make local tweaks to the config files. How do you do 
that? Let's see.

To make changes to mediagoblin.ini ::

    cp mediagoblin.ini mediagoblin_local.ini

To make changes to paste.ini ::

    cp paste.ini paste_local.ini

From here you should be able to make direct adjustments to the files,
and most of the commands described elsewhere in this manual will "notice"
your local config files and use those instead of the non-local version.

.. note::

   Note that all commands provide a way to pass in a specific config
   file also, usually by a ``-cf`` flag.


Common changes
==============

Enabling email notifications
----------------------------

You'll almost certainly want to enable sending email.  By default,
MediaGoblin doesn't really do this... for the sake of developer
convenience, it runs in "email debug mode".

To make MediaGoblin send email, you need a mailer daemon.

Change this in your ``mediagoblin.ini`` file::

    email_debug_mode = false

You should also change the "from" email address by setting
``email_sender_address``. For example::

    email_sender_address = "foo@example.com"

If you have more custom SMTP settings, you also have the following
options at your disposal, which are all optional, and do exactly what
they sound like.

- email_smtp_host
- email_smtp_port
- email_smtp_user
- email_smtp_pass

Changing data directory
-----------------------

MediaGoblin by default stores your data in wherever ``data_basedir``.
This can be changed by changing the value in your ``mediagoblin.ini`` file
for example::

    [DEFAULT]
    data_basedir = "/var/mediagoblin/user_data"

For efficiency reasons MediaGoblin doesn't serve these files itself and
instead leaves that to the webserver. You will have to alter the location
to match the path in ``data_basedir``.

If you use ``lazyserver.sh`` you need to change the ``paste.ini`` file::

    [app:mediagoblin]
    /mgoblin_media = /var/mediagoblin/user_data

If you use nginx you need to change the config::

     # Instance specific media:
     location /mgoblin_media/ {
         alias /var/mediagoblin/user_data;
     }

Once you have done this you will need to move any existing media you had in the
old directory to the new directory so existing media still can be displayed.

All other configuration changes
-------------------------------

To be perfectly honest, there are quite a few options and we haven't had
time to document them all.

So here's a cop-out section saying that if you get into trouble, hop
onto IRC and we'll help you out.  Details for the IRC channel is on the
`join page`_ of the website.

.. _join page: http://mediagoblin.org/join/




Celery
======

FIXME: List Celery configuration here.
