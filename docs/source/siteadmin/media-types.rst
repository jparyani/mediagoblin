.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _media-types-chapter:

====================
Enabling Media Types
====================

In the future, there will be all sorts of media types you can enable,
but in the meanwhile there are two additional media type: video and
ascii art.

First, you should probably read ":doc:`configuration`" to make sure
you know how to modify the mediagoblin config file.

Video
=====

To enable video, first install gstreamer and the python-gstreamer
bindings (as well as whatever gstremaer extensions you want,
good/bad/ugly).  On Debianoid systems::

    sudo apt-get install python-gst0.10 gstreamer0.10-plugins-{base,bad,good,ugly} \
        gstreamer0.10-ffmpeg

Next, modify (and possibly copy over from ``mediagoblin.ini``) your
``mediagoblin_local.ini``.  In the ``[mediagoblin]`` section, add
``mediagoblin.media_types.video`` to the ``media_types`` list.

For example, if your system supported image and video media types, then
the list would look like this::

    media_types = mediagoblin.media_types.image, mediagoblin.media_types.video

Now you should be able to submit videos, and mediagoblin should
transcode them.

.. note::

   You almost certainly want to separate Celery from the normal
   paste process or your users will probably find that their connections
   time out as the video transcodes.  To set that up, check out the
   ":doc:`production-deployments`" section of this manual.


Ascii art
=========

To enable ascii art support, first install the
`chardet <http://pypi.python.org/pypi/chardet>`_
library, which is necessary for creating thumbnails of ascii art::

    ./bin/easy_install chardet


Next, modify (and possibly copy over from ``mediagoblin.ini``) your
``mediagoblin_local.ini``.  In the ``[mediagoblin]`` section, add
``mediagoblin.media_types.ascii`` to the ``media_types`` list.

For example, if your system supported image and ascii art media types, then
the list would look like this::

    media_types = mediagoblin.media_types.image, mediagoblin.media_types.ascii

Now any .txt file you uploaded will be processed as ascii art!
