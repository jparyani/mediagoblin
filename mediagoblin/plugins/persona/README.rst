.. _persona-chapter:

================
 persona plugin
================

The persona plugin allows users to login to you GNU MediaGoblin instance using
`Mozilla Persona`_.

This plugin can be enabled alongside :ref:`openid-chapter` and
:ref:`basic_auth-chapter`.

.. note::
    When :ref:`basic_auth-chapter` is enabled alongside this persona plugin, and
    a user creates an account using their persona. If they would like to add a
    password to their account, they can use the forgot password feature to do
    so.

.. _Mozilla Persona: https://www.mozilla.org/en-US/persona/

Set up the persona plugin
=========================

1. Install the ``requests`` package.

2. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.persona]]

3. Run::

        gmg dbupdate

   in order to create and apply migrations to any database tables that the
   plugin requires.

4. Run::

        gmg assetlink

   in order to persona's static assets.
