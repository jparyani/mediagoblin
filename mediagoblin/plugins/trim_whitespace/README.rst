=======================
 Trim whitespace plugin
=======================

Mediagoblin templates are written with 80 char limit for better
readability. However that means that the html output is very verbose
containing LOTS of whitespace. This plugin inserts a Middleware that
filters out whitespace from the returned HTML in the Response() objects.

Simply enable this plugin by putting it somewhere where python can reach it and put it's path into the [plugins] section of your mediagoblin.ini or mediagoblin_local.ini like for example this:

    [plugins]
    [[mediagoblin.plugins.trim_whitespace]]

There is no further configuration required. If this plugin is enabled,
all text/html documents should not have lots of whitespace in between
elements, although it does a very naive filtering right now (just keep
the first whitespace and delete all subsequent ones).

Nonetheless, it is a useful plugin that might serve as inspiration for
other plugin writers.

It was originally conceived by Sebastian Spaeth. It is licensed under
the GNU AGPL v3 (or any later version) license.

