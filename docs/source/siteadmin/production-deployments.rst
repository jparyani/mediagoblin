.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

=========================================
Considerations for Production Deployments
=========================================

This document contains a number of suggestions for deploying
MediaGoblin in actual production environments. Consider
":doc:`deploying`" for a basic overview of how to deploy MediaGoblin.

Deploy with Paste
-----------------

The MediaGoblin WSGI application instance you get with ``./lazyserver.sh`` is
not ideal for a production MediaGoblin deployment. Ideally, you should be able
to use an "init" or "control" script to launch and restart the MediaGoblin
process.

Use the following command as the basis for such a script:

.. code-block:: bash

    CELERY_ALWAYS_EAGER=true \
     /srv/mediagoblin.example.org/mediagoblin/bin/paster serve \
     /srv/mediagoblin.example.org/mediagoblin/paste.ini \
     --pid-file=/var/run/mediagoblin.pid \
     --server-name=fcgi fcgi_host=127.0.0.1 fcgi_port=26543

The above configuration places MediaGoblin in "always eager" mode
with Celery, this means that submissions of content will be processed
synchronously, and the user will advance to the next page only after
processing is complete. If we take Celery out of "always eager mode,"
the user will be able to immediately return to the MediaGoblin site
while processing is ongoing. In these cases, use the following command
as the basis for your script:

.. code-block:: bash

    CELERY_ALWAYS_EAGER=false \
     /srv/mediagoblin.example.org/mediagoblin/bin/paster serve \
     /srv/mediagoblin.example.org/mediagoblin/paste.ini \
     --pid-file=/var/run/mediagoblin.pid \
     --server-name=fcgi fcgi_host=127.0.0.1 fcgi_port=26543

Separate Celery
---------------

MediaGoblin uses `Celery`_ to handle heavy and long-running tasks. Celery can
be launched in two ways:

1.  Embedded in the MediaGoblin WSGI application [#f-mediagoblin-wsgi-app]_.
    This is the way ``./lazyserver.sh`` does it for you. It's simple as you
    only have to run one process. The only bad thing with this is that the
    heavy and long-running tasks will run *in* the webserver, keeping the user
    waiting each time some heavy lifting is needed as in for example processing
    a video. This could lead to problems as an aborted connection will halt any
    processing and since most front-end web servers *will* terminate your
    connection if it doesn't get any response from the MediaGoblin WSGI
    application in a while.

2.  As a separate process communicating with the MediaGoblin WSGI application
    via a `broker`_. This offloads the heavy lifting from the MediaGoblin WSGI
    application and users will be able to continue to browse the site while the
    media is being processed in the background.

.. _`broker`: http://docs.celeryproject.org/en/latest/getting-started/brokers/
.. _`celery`: http://www.celeryproject.org/


.. [#f-mediagoblin-wsgi-app] The MediaGoblin WSGI application is the part that
    of MediaGoblin that processes HTTP requests.

To launch Celery separately from the MediaGoblin WSGI application:

1.  Make sure that the ``CELERY_ALWAYS_EAGER`` environment variable is unset or
    set to ``false`` when launching the MediaGoblin WSGI application.
2.  Start the ``celeryd`` main process with

    .. code-block:: bash

        CELERY_CONFIG_MODULE=mediagoblin.init.celery.from_celery ./bin/celeryd

.. _sentry:

Set up sentry to monitor exceptions
-----------------------------------

We have a plugin for `raven`_ integration, see the ":doc:`/plugindocs/raven`"
documentation.

.. _`raven`: http://raven.readthedocs.org


.. _init-script:

Use an Init Script
------------------

Look in your system's ``/etc/init.d/`` or ``/etc/rc.d/`` directory for
examples of how to build scripts that will start, stop, and restart
MediaGoblin and Celery. These scripts will vary by
distribution/operating system.

These are scripts provided by the MediaGoblin community: 

Debian
  * `GNU MediaGoblin init scripts
    <https://github.com/joar/mediagoblin-init-scripts>`_
    by `Joar Wandborg <http://wandborg.se>`_

Arch Linux
  * `MediaGoblin - ArchLinux rc.d scripts
    <http://whird.jpope.org/2012/04/14/mediagoblin-archlinux-rcd-scripts>`_
    by `Jeremy Pope <http://jpope.org/>`_
  * `Mediagoblin init script on Archlinux
    <http://chimo.chromic.org/2012/03/01/mediagoblin-init-script-on-archlinux/>`_
    by `Chimo <http://chimo.chromic.org/>`_

.. TODO insert init script here
.. TODO are additional concerns ?
   .. Other Concerns
   .. --------------
