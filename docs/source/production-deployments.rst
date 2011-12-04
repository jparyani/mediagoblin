=========================================
Considerations for Production Deployments
=========================================

This document contains a number of suggestions for deploying
MediaGoblin in actual production environments. Consider
":doc:`deploying`" for a basic overview of how to deploy Media
Goblin.

Celery
------

While the ``./lazyserer.sh`` configuration provides an efficient way to
start using a MediaGoblin instance, it is not suitable for production
deployments for several reasons:

1. In nearly every scenario, work on the Celery queue will need to
   balance with the demands of other processes, and cannot proceed
   synchronously. This is a particularly relevant problem if you use
   MediaGoblin to host Video content.

2. Processing with Celery ought to be operationally separate from the
   MediaGoblin application itself, this simplifies management and
   support better workload distribution.

3. ... additional reason here. ....

Build an :ref:`init script <init-script>` around the following
command.

      CELERY_CONFIG_MODULE=mediagoblin.init.celery.from_celery ./bin/celeryd

Modify your existing MediaGoblin and application init scripts, if
necessary, to prevent them from starting their own ``celeryd``
processes.

.. _init-script:

Use an Init Script
-------------------

TODO insert init script here

Other Concerns
--------------

TODO What are they?

