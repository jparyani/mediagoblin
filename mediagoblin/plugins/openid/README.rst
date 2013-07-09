.. _openid-chapter:

===================
 openid plugin
===================

The openid plugin allows user to login to your GNU Mediagoblin instance using
their openid url.

This plugin can be enabled alongside :ref:`basic_auth-chapter` and
:ref:`persona-chapter`.

.. note::
    When :ref:`basic_auth-chapter` is enabled alongside this openid plugin, and
    a user creates an account using their openid. If they would like to add a
    password to their account, they can use the forgot password feature to do
    so.


Set up the openid plugin
============================

1. Install the ``python-openid`` package.

2. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.openid]]

3. Run::

        gmg dbupdate

   in order to create and apply migrations to any database tables that the
   plugin requires.
