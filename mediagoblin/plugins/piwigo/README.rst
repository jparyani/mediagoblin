===================
 piwigo api plugin
===================

.. danger::
   This plugin does not work.
   It might make your instance unstable or even insecure.
   So do not use it, unless you want to help to develop it.

.. warning::
   You should not depend on this plugin in any way for now.
   It might even go away without any notice.

Okay, so if you still want to test this plugin,
add the following to your mediagoblin_local.ini:

.. code-block:: ini

   [plugins]
   [[mediagoblin.plugins.piwigo]]

Then try to connect using some piwigo client.
There should be some logging, that might help.
