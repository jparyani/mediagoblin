.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

Pump.io supports a number of different interactions that can happen against
media. Theser are commenting, liking/favoriting and (re-)sharing. Currently
MediaGoblin supports just commenting although other interactions will come at
a later date.

--------------
How to comment
--------------

.. warning:: Commenting on a comment currently is NOT supported.

Commenting is done by posting a comment activity to the users feed. The
activity should look similiar to::

    {
        "verb": "post",
        "object": {
            "objectType": "comment",
            "inReplyTo": <media>
        }
    }

This is where `<media>` is the media object you have got with from the server.

----------------
Getting comments
----------------

The media object you get back should have a `replies` section. This should
be an object which contains the number of replies and if there are any (i.e.
number of replies > 0) then `items` will include an array of every item::

    {
        "totalItems": 2,
        "items: [
            {
                "id": 1,
                "objectType": "comment",
                "content": "I'm a comment ^_^",
                "author": <author user object>
            },
            {
                "id": 4,
                "objectType": "comment",
                "content": "Another comment! Blimey!",
                "author": <author user object>
            }
        ],
        "url": "http://some.server/api/images/1/comments/"
    }


