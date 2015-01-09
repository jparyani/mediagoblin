.. MediaGoblin Documentation

   Written in 2015 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

==========
Activities
==========

.. contents:: Sections
   :local:

GNU MediaGoblin uses `Activity Streams 1.0 <http://activitystrea.ms>`_ JSON
format to represent activities or events that happen. There are several
components to Activity Streams.

Objects
=======
These represent "things" in MediaGoblin such as types of media, comments, collections
of other objects, etc. There are attributes all objects have and some attributes which
are specific to certain objects.

Example
-------
a representation of an image object::

    {
        "id": "https://gmg.server.tld/api/image/someidhere",
        "objectType": "image",
        "content": "My lovely image",
        "image": {
            "url": "https://gmg.server.tld/mgoblin_media/media_entries/23/some_image.jpg",
            "height": 1000,
            "width": 500
        },
        "author": {
            "id": "acct:someone@gmg.server.tld"
        }
    }

This has both attributes which are on all objects (e.g. ``objectType`` and ``id``)
and attributes which are on only images (e.g. ``image``).

Activities
==========
This is something which happens such as: commenting on an image, uploading an image, etc.
these always have a ``verb`` which describes what kind of activity it is and they always have
an ``object`` associated with them.

Example
-------
A activity which describes the event of posting a new image::

    {
        "id": "https://gmg.server.tld/api/activity/someidhere",
        "verb": "post",
        "object": {
            "id": "https://gmg.server.tld/api/comment/someid",
            "objectType": "comment",
            "content": "What a wonderful picture you have there!",
            "inReplyTo": {
                "id": "https://gmg.server.tld/api/image/someidhere"
            }
        },
        "author": {
            "id": "acct:someone@gmg.server.tld"
        }
    }

Collections
===========

These are ordered lists which contain objects. Currently in GNU MediaGoblin they are used
to represent "albums" or collections of media however they can represent anything. They will
be used in the future to represent lists/groups of users which you can send activities to.

Example
^^^^^^^
A collection which contains two images::

    {
        "id": "https://gmg.server.tld/api/collection/someidhere",
        "totalItems": 2,
        "url": "http://gmg.server.tld/u/someone/collection/cool-album/",
        "items": [
			{
			   "id": "https://gmg.server.tld/api/image/someidhere",
			   "objectType": "image",
			   "content": "My lovely image",
			   "image": {
			       "url": "https://gmg.server.tld/mgoblin_media/media_entries/23/some_image.jpg",
			       "height": 1000,
			       "width": 500
			   },
			   "author": {
			       "id": "acct:someone@gmg.server.tld"
			   }
			},
			{
			   "id": "https://gmg.server.tld/api/image/someother",
			   "objectType": "image",
			   "content": "Another image for you",
			   "image": {
			       "url": "https://gmg.server.tld/mgoblin_media/media_entries/24/some_other_image.jpg",
			       "height": 1000,
			       "width": 500
			   },
			   "author": {
			       "id": "acct:someone@gmg.server.tld"
			   }
			}
        ]
    }

Feeds
-----

There are several feeds which can be read and posted to as part of the API. Some
of the feeds are still a work in progress however a lot of them are present for
compatibility.

They also support certain GET parameters which allow you to control the stream.
These are:

+-------------+----------+----------+----------------------------------+
| Parameter   | Default  | Limit    | Description                      |
+=============+==========+==========+==================================+
| count       | 20       | 200      | Number of activities to return   |
+-------------+----------+----------+----------------------------------+
| offset      | 0        | No limit | Offset of collection             |
+-------------+----------+----------+----------------------------------+

.. warning::
   Activities are added to the beginning of collection so using count and
   offset is a bad way of doing pages.

.. important::
   Due to the way we're currently doing deletes in MediaGoblin some activities
   are broken and are skipped. This means the number you specify in the count
   is NOT always the number of activities returned.


Inbox
^^^^^

**Endpoint:** `/api/user/<username>/inbox`

This feed can be read by user to see what media has been sent to them.
MediaGoblin currently doesn't have the ability to sent media to anyone
as all media is public, all media on that instance should show up in the
users inbox.

There are also subsets of the inbox which are:

Major
"""""
**Endpoint:** ``/api/user/<username>/inbox/major``

This contains all major changes such as new objects being posted. Currently
comments exist in this feed, in the future they will be moved to the minor feed.

Minor
"""""
**Endpoint:** ``/api/user/<username>/inbox/minor``

This contains minor changes such as objects being updated or deleted. This feed
should have comments in it, currently they are listed under major, in the future
they will exist in this endpoint.

Direct
""""""
**Endpoint:** ``/api/user/<username>/inbox/direct``

Currently this is just a mirror of the regular inbox for compatibility with
pump.io. In the future this will contain all objects specifically addressed to
the user.

Direct major
""""""""""""
**Endpoint:** ``/api/user/<username>/inbox/direct/major``

Currently this is just a mirror of the major inbox for compatibility with
pump.io. In the future this will contain all major activities which are
specifically addressed to the user.

Direct minor
""""""""""""
**Endpoint:** ``/api/user/<username>/inbox/direct/minor``

Currently this is just a mirror of the minor inbox for compatibility with
pump.io. In the future this will contain all minor activities which are
specifically addressed to the user.

Feed (outbox)
^^^^^^^^^^^^^
**Endpoint:** ``/api/user/<username>/feed``

This is where the client should post new activities. It can be read by the
user to see what they have posted. This will only contain content they have
authored or shared (sharing will come in the future).
