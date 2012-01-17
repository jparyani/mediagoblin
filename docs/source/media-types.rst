.. _media-types-chapter:

====================
Enabling Media Types
====================

In the future, there will be all sorts of media types you can enable,
but in the meanwhile there's only one additional media type: video.

First, you should probably read ":doc:`configuration`" to make sure
you know how to modify the mediagoblin config file.

Video
=====

To enable video, first install gstreamer and the python-gstreamer
bindings (as well as whatever gstremaer extensions you want,
good/bad/ugly).  On Debianoid systems::

    sudo apt-get install python-gst0.10

Next, modify (and possibly copy over from ``mediagoblin.ini``) your
``mediagoblin_local.ini``.  Uncomment this line in the ``[mediagoblin]``
section::

    media_types = mediagoblin.media_types.image, mediagoblin.media_types.video

Now you should be able to submit videos, and mediagoblin should
transcode them.

Note that you almost certainly want to separate Celery from the normal
paste process or your users will probably find that their connections
time out as the video transcodes.  To set that up, check out the
":doc:`production-deployments`" section of this manual.
