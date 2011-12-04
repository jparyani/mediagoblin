=========================================
Considerations for Production Deployments
=========================================

This document contains a number of suggestions for deploying
MediaGoblin in actual production environments. Consider
":doc:`deploying`" for a basic overview of how to deploy Media
Goblin.

Deploy with Paste
-----------------

The instance configured with ``./lazyserver.sh`` is not ideal for a
production MediaGoblin deployment. Ideally, you should be able to use
an "init" or "control" script to launch and restart the MediaGoblin
process.

Use the following command as the basis for such a script: ::

       CELERY_ALWAYS_EAGER=true \
        /srv/mediagoblin.example.org/mediagoblin/bin/paster serve \
        /srv/mediagoblin.example.org/mediagoblin/paste.ini \
        --pid-file=/var/run/mediagoblin.pid \
        --server-name=fcgi fcgi_host=127.0.0.1 fcgi_port=26543 \

The above configuration places MediaGoblin in "always eager" mode
with Celery, this means that submissions of content will be processed
synchronously, and the user will advance to the next page only after
processing is complete. If we take Celery out of "always eager mode,"
the user will be able to immediately return to the MediaGoblin site
while processing is ongoing. In these cases, use the following command
as the basis for your script: ::

       CELERY_ALWAYS_EAGER=false \
        /srv/mediagoblin.example.org/mediagoblin/bin/paster serve \
        /srv/mediagoblin.example.org/mediagoblin/paste.ini \
        --pid-file=/var/run/mediagoblin.pid \
        --server-name=fcgi fcgi_host=127.0.0.1 fcgi_port=26543 \

Separate Celery
---------------

While the ``./lazyserer.sh`` configuration provides an efficient way to
start using a MediaGoblin instance, it is not suitable for production
deployments for several reasons:

In nearly every scenario, work on the Celery queue will need to
balance with the demands of other processes, and cannot proceed
synchronously. This is a particularly relevant problem if you use
MediaGoblin to host video content. Processing with Celery ought to be
operationally separate from the MediaGoblin application itself, this
simplifies management and support better workload distribution.

Basically, if you're doing anything beyond a trivial workload, such as
image hosting for a small set of users, or have limited media types
such as "ASCII art" or icon sharing, you will need to run ``celeryd``
as a separate process.

Build an :ref:`init script <init-script>` around the following
command.

      CELERY_CONFIG_MODULE=mediagoblin.init.celery.from_celery ./bin/celeryd

Modify your existing MediaGoblin and application init scripts, if
necessary, to prevent them from starting their own ``celeryd``
processes.

.. _init-script:

Use an Init Script
------------------

Look in your system's ``/etc/init.d/`` or ``/etc/rc.d/`` directory for
examples of how to build scripts that will start, stop, and restart
MediaGoblin and Celery. These scripts will vary by
distribution/operating system. In the future, MediaGoblin will provide
example scripts as examples.

.. TODO insert init script here
.. TODO are additional concernts ?
   .. Other Concerns
   .. --------------
