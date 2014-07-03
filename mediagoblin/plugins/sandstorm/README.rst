.. MediaGoblin Documentation

   Written in 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _sandstorm-plugin:

=============
 sandstorm plugin
=============

.. Warning::
   This plugin is not compatible with the other authentication plugins.

This plugin allow your GNU Mediagoblin instance to authenticate when inside a
sandstorm grain

Set up the sandstorm plugin
======================

1. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.sandstorm]]
