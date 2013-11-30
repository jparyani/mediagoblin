.. MediaGoblin Documentation

   Written in 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _ldap-plugin:

=============
 ldap plugin
=============

.. Warning::
   This plugin is not compatible with the other authentication plugins.

This plugin allow your GNU Mediagoblin instance to authenticate against an
LDAP server.

Set up the ldap plugin
======================

1. Install the ``python-ldap`` package.

2. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.ldap]]

Configuring the ldap plugin
===========================

This plugin allows you to use multiple ldap servers for authentication.

In order to configure a server, add the following to you MediaGoblin .ini file
under the ldap plugin:: 

    [[mediagoblin.plugins.ldap]]
    [[[server1]]]
    LDAP_SERVER_URI = 'ldap://ldap.testathon.net:389'
    LDAP_USER_DN_TEMPLATE = 'cn={username},ou=users,dc=testathon,dc=net'
    [[[server2]]]
    ...

Make any necessary changes to the above to work with your sever. Make sure
``{username}`` is where the username should be in LDAP_USER_DN_TEMPLATE.
   
If you would like to fetch the users email from the ldap server upon account
registration, add ``LDAP_SEARCH_BASE = 'ou=users,dc=testathon,dc=net'`` and
``EMAIL_SEARCH_FIELD = 'mail'`` under you server configuration in your
MediaGoblin .ini file.

.. Warning::
   By default, this plugin provides no encryption when communicating with the
   ldap servers. If you would like to use an SSL connection, change
   LDAP_SERVER_URI to use ``ldaps://`` and whichever port you use. Default ldap
   port for SSL connections is 636. If you would like to use a TLS connection,
   add ``LDAP_START_TLS = 'true'`` under your server configuration in your
   MediaGoblin .ini file.
