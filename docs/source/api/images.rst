.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

==================
Uploading an Image
==================

To use any the APIs mentioned in this document you will required :doc:`oauth`

Uploading and posting an image requiest you to make two requests, one of which
submits the image to the server, the other of which will post the meta data.

To upload an image you should use the URI `/api/user/<username>/uploads`.

A POST request should be made to the image upload URI submitting at least two header:

* `Content-Type` - This being a valid mimetype for the image.
* `Content-Length` - size in bytes of the image.

The binary image data should be submitted as POST data to the image upload URI.
You will get back a JSON encoded response which will look similiar to::

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

Submit to feed
==============

The next request you will probably wish to make is to post the image to your
feed, this currently in GNU MediaGoblin will just show it visably on the website.
In the future it will allow you to specify whom should see this image.

The URL you will want to make a POST request to to is `/api/user/<username>/feed`

You first should do a post to the feed URI with some of the information you got
back from the above request (which uploaded the image). The request should look
something like::

    {
        "verb": "post",
        "object": {
            "id": "https://<server>/api/image/6_K9m-2NQFi37je845c83w",
            "objectType": "image"
        }
    }

(Any other data submitted **will** be ignored)

Finally if you wish to set a title, description and licence you will need to do
and update request to the endpoint, the following attributes can be submitted:

+--------------+---------------------------------------+-------------------+
| Name         | Description                           | Required/Optional |
+==============+=======================================+===================+
| displayName  | This is the title for the image       | Optional          |
+--------------+---------------------------------------+-------------------+
| content      | This is the description for the image | Optional          |
+--------------+---------------------------------------+-------------------+
| license      | This is the licence to be used        | Optional          |
+--------------+---------------------------------------+-------------------+

.. note:: license attribute is mediagoblin specific, pump.io does not support this attribute


The update request should look something similiar to::

    {
        "verb": "update",
        "object": {
            "displayName": "My super awesome image!",
            "content": "The awesome image I took while backpacking to modor",
            "license": "creativecommons.org/licenses/by-sa/3.0/",
            "id": "https://<server>/api/image/6_K9m-2NQFi37je845c83w",
            "objectType": "image"
        }
    }

(Again, any other data submitted **will** be ignored).
