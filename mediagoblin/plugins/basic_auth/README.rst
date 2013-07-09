.. _basic_auth-chapter:

===================
 basic_auth plugin
===================

The basic_auth plugin is enabled by default in mediagoblin.ini. This plugin
provides basic username and password authentication for GNU Mediagoblin.

This plugin can be enabled alongside :ref:`openid-chapter` and
:ref:`persona-chapter`.

Set up the basic_auth plugin
============================

1. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.basic_auth]]

2. Run::

        gmg assetlink

   in order to link basic_auth's static assets
