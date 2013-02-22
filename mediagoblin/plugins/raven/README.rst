==============
 raven plugin
==============

.. warning::
    The raven plugin only sets up raven for celery. To enable raven for paster,
    see the deployment docs section on setting up exception monitoring.


Set up the raven plugin
=======================

1. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.raven]]
    sentry_dsn = <YOUR SENTRY DSN>
