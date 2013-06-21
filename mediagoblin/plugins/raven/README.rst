==============
 raven plugin
==============

.. _raven-setup:

Warning: this plugin is somewhat experimental.

Set up the raven plugin
=======================

1. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.raven]]
    sentry_dsn = <YOUR SENTRY DSN>
    # Logging is very high-volume, set to 0 if you want to turn off logging
    setup_logging = 1
