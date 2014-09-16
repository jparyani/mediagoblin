.. MediaGoblin Documentation

   Written in 2014 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.


===============================
Documentation on Built-in Hooks
===============================

This section explains built-in hooks to MediaGoblin.


What hooks are available?
=========================

'collection_add_media'
----------------------

This hook is used by ``add_media_to_collection``
in ``mediagoblin.user_pages.lib``.
It gets a ``CollectionItem`` as its argument.
It's the newly created item just before getting commited.
So the item can be modified by the hook, if needed.
Changing the session regarding this item is currently
undefined behaviour, as the SQL Session might contain other
things.
