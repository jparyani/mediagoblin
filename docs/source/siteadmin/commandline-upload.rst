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

If you're a site administrator and have access to the server then you
can use the 'addmedia' task. If you're just a user and want to upload
media by the command line you can. This can be done with the pump.io
API. There is `p <https://github.com/xray7224/p/>`_, which will allow you
to easily upload media from the command line, follow p's docs to do that.

To use the addmedia command::

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
The location column
-------------------
The location column is the one column that is absolutely necessary for
uploading your media. This gives a path to each piece of media you upload. This
can either a path to a local file or a direct link to remote media (with the
link in http format). As you can see in the example above the (fake) media was
stored remotely on "www.example.net".

Other internal nodes
--------------------
There are other columns which can be used by the script to provide information.
These are not stored as part of the media's metadata. You can use these columns to
provide default information for your media entry, but as you'll see below, it's
just as easy to provide this information through the correct metadata columns.

- **id** is used to identify the media entry to the user in case of an error in the batchaddmedia script.
- **license** is used to set a license for your piece a media for mediagoblin's use. This must be a URI.
- **title** will set the title displayed to mediagoblin users.
- **description** will set a description of your media.

Metadata columns
----------------
Other columns can be used to provide detailed metadata about each media entry.
Our metadata system accepts any information provided for in the
`RDFa Core Initial Context`_, and the batchupload script recognizes all of the
resources provided within it.

.. _RDFa Core Initial Context: http://www.w3.org/2011/rdfa-context/rdfa-1.1

The uploader may include the metadata for each piece of media, or
leave them blank if they want to. A few columns from `Dublin Core`_ are
notable because the batchaddmedia script also uses them to set the default
information of uploaded media entries.

.. _Dublin Core: http://wiki.dublincore.org/index.php/User_Guide

- **dc:title** sets a title for your media entry.
- **dc:description** sets a description of your media entry.

If both a metadata column and an internal node for the title are provided, mediagoblin
will use the internal node as the media entry's display name. This makes it so
that if you want to display a piece of media with a different title
than the one provided in its metadata, you can just provide different data for
the 'dc:title' and 'title' columns. The same is true of the 'description' and
'dc:description'.
