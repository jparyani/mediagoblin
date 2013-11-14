.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

======================
Command-line uploading
======================

Want to submit media via the command line?  It's fairly easy to do::

  ./bin/gmg addmedia username your_media.jpg

This will submit the file "your_media.jpg" to be a media entry
associated with the user "username".

You can get help on all the available options by running::

  ./bin/gmg addmedia --help

Here's a longer example that makes use of more options::

  ./bin/gmg addmedia aveyah awesome_spaceship.png \
      --title "My awesome spaceship" \
      --description "Flying my awesome spaceship, since I'm an awesome pilot" \
      --license "http://creativecommons.org/licenses/by-sa/3.0/" \
      --tags "spaceships, pilots, awesome" \
      --slug "awesome-spaceship"

You can also pass in the `--celery` option if you would prefer that
your media be passed over to celery to be processed rather than be
processed immediately.

