.. MediaGoblin Documentation

   Written in 2015 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. info:: Currently only image uploading is supported.

=======
Objects
=======

Using any the APIs mentioned in this document you will required
:doc:`authentication`. There are many ways to interact with objects, some of
which aren't supported yet by mediagoblin such as liking or sharing objects
however you can interact with them by updating them, deleting them and
commenting on them.

Posting Objects
---------------

For the most part you should be able to post objects by creating the JSON
representation of the object on an activity and posting that to the user's
feed (outbox). Images however are slightly different and there are more steps
to it as you might imagine.

Using posting a comment as an example, I'll show you how to post the object
to GNU MediaGoblin or pump.io. I first need to create the JSON representation
of the activity with the object but without the ID, URL, published or updated
timestamps or any other data the server creates. My activity comment is::

    {
        "verb": "post",
        "object": {
            "objectType": "comment",
            "content": "This is my comment to be posted",
            "inReplyTo": {
                "id": "https://<server>/api/image/1"
            }
        }
    }

This should be posted to the users feed (outbox) which you can find out about
:doc:`activities`. You will get back the full activity containing all of
attributes including ID, urls, etc.

Posting Media
~~~~~~~~~~~~~

Posting media is a special case from posting all other objects. This is because
you need to submit more than just the JSON image representation, you need to
actually subject the image itself. There is also strange behavour around media
postings where if you want to give the media you're posting a title or
description you need to peform an update too. A full media posting in order of
steps to do is as follows:

1) Uploads the data to the server
2) Post media to feed
3) Update media to have title, description, license, etc. (optional)

This could be condensed into a 2-step process however this would need to happen
upstream. If you would like to contribute to changing this upstream there is
an issue open: https://github.com/e14n/pump.io/issues/657

To upload media you should use the URL `/api/user/<username>/uploads`.

A POST request should be made to the media upload URL submitting at least two
headers:

* `Content-Type` - This being a valid mimetype for the media.
* `Content-Length` - size in bytes of the media.

The media data should be submitted as POST data to the image upload URL.
You will get back a JSON encoded response which will look similar to::

    {
        "updated": "2014-01-11T09:45:48Z",
        "links": {
            "self": {
                "href": "https://<server>/image/4wiBUV1HT8GRqseyvX8m-w"
            }
        },
        "fullImage": {
            "url": "https://<server>//uploads/<username>/2014/1/11/V3cBMw.jpg",
            "width": 505,
            "height": 600
        },
        "replies": {
            "url": "https://<server>//api/image/4wiBUV1HT8GRqseyvX8m-w/replies"
        },
        "image": {
            "url": "https://<server>/uploads/<username>/2014/1/11/V3cBMw_thumb.jpg",
            "width": 269,
            "height": 320
        },
        "author": {
            "preferredUsername": "<username>",
            "displayName": "<username>",
            "links": {
                "activity-outbox": {
                    "href": "https://<server>/api/user/<username>/feed"
                },
                "self": {
                    "href": "https://<server>/api/user/<username>/profile"
                },
                "activity-inbox": {
                    "href": "https://<server>/api/user/<username>/inbox"
                }
            },
            "url": "https://<server>/<username>",
            "updated": "2013-08-14T10:01:21Z",
            "id": "acct:<username>@<server>",
            "objectType": "person"
        },
        "url": "https://<server>/<username>/image/4wiBUV1HT8GRqseyvX8m-w",
        "published": "2014-01-11T09:45:48Z",
        "id": "https://<server>/api/image/4wiBUV1HT8GRqseyvX8m-w",
        "objectType": "image"
    }

The main things in this response is `fullImage` which contains `url` (the URL
of the original image - i.e. fullsize) and `image` which contains `url` (the URL
of a thumbnail version).

.. warning:: Media which have been uploaded but not submitted to a feed will
             periodically be deleted.

Once you've got the image object back you will need to submit the post
activity to the feed. This is exactly the same process as posting any other
object described above. You create a post activity and post that to the feed
(outbox) endpoint. The post activity looks like::

    {
        "verb": "post",
        "object": {
            "id": "https://<server>/api/image/4wiBUV1HT8GRqseyvX8m-w",
            "objectType": "image"
        }
    }

You will get back the full activity, unlike above however if you wish to
submit `displayName` (title) or `content` (description) information you need
to create an update activity and post that to the feed after you have posted
the image. An update activity would look like::

    {
        "verb": "update",
        "object": {
            "id": "https://<server>/api/image/4wiBUV1HT8GRqseyvX8m-w",
            "displayName": "This is my title",
            "content": "This is my description",
            "objectType": "image"
        }
    }

Updating Objects
----------------

If you would like to edit or update an object you can do so by submitting an
update activity. An update to a comment might look like::

    {
        "verb": "update",
        "object": {
            "id": "https://<server>/api/comment/1",
            "objectType": "comment",
            "content": "This is my new updated comment!"
        }
    }

This should be posted to the feed (outbox). You will get back the full update
activity in response.

Deleting Objects
----------------

Objects can be deleted by submitting a delete activity to the feed. A delete
object for a comment looks like::

    {
        "verb": "delete",
        "object": {
            "id": "https://<server>/api/comment/id",
            "objectType": "comment"
        }
    }

You should get the full delete activity in response.

.. warning::
    While deletion works, currently because of the way deletion is implemented
    deletion either via the API or the webUI causes any activities to be broken
    and will be skipped and unaccessible. A migration to remove the broken
    activities will come in a future release when soft-deletion has been
    implemented.

Posting Comments
----------------

Comments currently can only be on media objects, this however will change in
future versions of MediaGoblin to be inline with pump.io and Activity Streams
1.0 which allow comments to be on any object including comments themselves.

If you want to submit a comment on an object it's very easy, it's just like
posting any other object except you use the `inReplyTo` attribute which
specifies the object you are commenting on. The `inReplyTo` needs to contain
the object or specifically the ID of it.

Example of comment on an image::

    {
        "verb": "post",
        "object": {
            "content": "My comment here",
            "inReplyTo": {
                "id": "https://<server>/api/image/72"
            }
        }
    }

This should be posted to a feed and you will get back the full activity object
as with any other object posting.
