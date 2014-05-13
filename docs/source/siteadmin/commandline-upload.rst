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

============================
Command-line batch uploading
============================

There's another way to submit media, and it can be much more powerful, although
it is a bit more complex.

  ./bin/gmg batchaddmedia admin /path/to/your/metadata.csv

This is an example of what a script may look like. The important part here is
that you have to create the 'metadata.csv' file.::

  media:location,dcterms:title,dcterms:creator,dcterms:type
  "http://www.example.net/path/to/nap.png","Goblin taking a nap",,"Image"
  "http://www.example.net/path/to/snore.ogg","Goblin Snoring","Me","Audio"

The above is an example of a very simple metadata.csv file. The batchaddmedia
script would read this and attempt to upload only two pieces of media, and would
be able to automatically name them appropriately.

The csv file
============
The media:location column
-------------------------
The media:location column is the one column that is absolutely necessary for
uploading your media. This gives a path to each piece of media you upload. This
can either a path to a local file or a direct link to remote media (with the
link in http format). As you can see in the example above the (fake) media was
stored remotely on "www.example.net".

Other columns
-------------
Other columns can be used to provide detailed metadata about each media entry.
Our metadata system accepts any information provided for in the
`RDFa Core Initial Context`_, and the batchupload script recognizes all of the
resources provided within it.

.. _RDFa Core Initial Context: http://www.w3.org/2011/rdfa-context/rdfa-1.1

The uploader may include the metadata for each piece of media, or
leave them blank if they want to. A few columns from `Dublin Core`_ are
notable because the batchaddmedia script uses them to set the default
information of uploaded media entries.

.. _Dublin Core: http://wiki.dublincore.org/index.php/User_Guide

- **dc:title** sets a title for your media entry. If this is left blank, the media entry will be named according to the filename of the file being uploaded.
- **dc:description** sets a description of your media entry. If this is left blank the media entry's description will not be filled in.
- **dc:rights** will set a license for your media entry `if` the data provided is a valid URI. If this is left blank 'All Rights Reserved' will be selected.

You can of course, change these values later.
