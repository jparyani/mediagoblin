===================
 Openid plugin
===================

The Openid plugin allows user to login to your GNU Mediagoblin instance using
their openid url.

This plugin can be enabled alongside :ref:`basic_auth-chapter` and
:ref:`persona-chapter`.

.. note::
    When :reg:`basic_auth-chapter` is enabled alongside this Openid plugin, and
    a user creates an account using their Openid. If they would like to add a
    password to their account, they can use the forgot password feature to do
    so.


Set up the Openid plugin
============================

1. Install the ``python-openid`` package.

2. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.openid]]

3. Run::

        gmg dbupdate

   in order to create and apply migrations to any database tables that the
   plugin requires.
