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
Media Types
====================

In the future, there will be all sorts of media types you can enable,
but in the meanwhile there are five additional media types: video, audio,
ascii art, STL/3d models, PDF and Document.

First, you should probably read ":doc:`configuration`" to make sure
you know how to modify the mediagoblin config file.

Enabling Media Types
====================

.. note::
    Media types are now plugins

Media types are enabled in your mediagoblin configuration file, typically it is
created by copying ``mediagoblin.ini`` to ``mediagoblin_local.ini`` and then
applying your changes to ``mediagoblin_local.ini``. If you don't already have a
``mediagoblin_local.ini``, create one in the way described.

Most media types have additional dependencies that you will have to install.
You will find descriptions on how to satisfy the requirements of each media type
on this page.

To enable a media type, add the the media type under the ``[plugins]`` section
in you ``mediagoblin_local.ini``. For example, if your system supported image
and video media types, then it would look like this::

    [plugins]
    [[mediagoblin.media_types.image]]
    [[mediagoblin.media_types.video]]

Note that after enabling new media types, you must run dbupdate like so::

    ./bin/gmg dbupdate

If you are running an active site, depending on your server
configuration, you may need to stop it first (and it's certainly a
good idea to restart it after the update).


How does MediaGoblin decide which media type to use for a file?
===============================================================

MediaGoblin has two methods for finding the right media type for an uploaded
file. One is based on the file extension of the uploaded file; every media type
maintains a list of supported file extensions. The second is based on a sniffing
handler, where every media type may inspect the uploaded file and tell if it
will accept it.

The file-extension-based approach is used before the sniffing-based approach,
if the file-extension-based approach finds a match, the sniffing-based approach
will be skipped as it uses far more processing power.


Video
=====

To enable video, first install gstreamer and the python-gstreamer
bindings (as well as whatever gstremaer extensions you want,
good/bad/ugly).  On Debianoid systems

.. code-block:: bash

    sudo apt-get install python-gst0.10 \
        gstreamer0.10-plugins-base \
        gstreamer0.10-plugins-bad \
        gstreamer0.10-plugins-good \
        gstreamer0.10-plugins-ugly \
        gstreamer0.10-ffmpeg


Add ``[[mediagoblin.media_types.video]]`` under the ``[plugins]`` section in
your ``mediagoblin_local.ini`` and restart MediaGoblin.

Run

.. code-block:: bash

    ./bin/gmg dbupdate

Now you should be able to submit videos, and mediagoblin should
transcode them.

.. note::

   You almost certainly want to separate Celery from the normal
   paste process or your users will probably find that their connections
   time out as the video transcodes.  To set that up, check out the
   ":doc:`production-deployments`" section of this manual.


Audio
=====

To enable audio, install the gstreamer and python-gstreamer bindings (as well
as whatever gstreamer plugins you want, good/bad/ugly), scipy and numpy are
also needed for the audio spectrograms.
To install these on Debianoid systems, run::

    sudo apt-get install python-gst0.10 gstreamer0.10-plugins-{base,bad,good,ugly} \
        gstreamer0.10-ffmpeg python-numpy python-scipy

The ``scikits.audiolab`` package you will install in the next step depends on the
``libsndfile1-dev`` package, so we should install it.
On Debianoid systems, run

.. code-block:: bash

    sudo apt-get install libsndfile1-dev

.. note::
    scikits.audiolab will display a warning every time it's imported if you do
    not compile it with alsa support. Alsa support is not necessary for the GNU
    MediaGoblin application but if you do not wish the alsa warnings from
    audiolab you should also install ``libasound2-dev`` before installing
    scikits.audiolab.

Then install ``scikits.audiolab`` for the spectrograms::

    ./bin/pip install scikits.audiolab

Add ``[[mediagoblin.media_types.audio]]`` under the ``[plugins]`` section in your
``mediagoblin_local.ini`` and restart MediaGoblin.

Run

.. code-block:: bash

    ./bin/gmg dbupdate

You should now be able to upload and listen to audio files!


Ascii art
=========

To enable ascii art support, first install the
`chardet <http://pypi.python.org/pypi/chardet>`_
library, which is necessary for creating thumbnails of ascii art

.. code-block:: bash

    ./bin/easy_install chardet


Next, modify (and possibly copy over from ``mediagoblin.ini``) your
``mediagoblin_local.ini``.  In the ``[plugins]`` section, add
``[[mediagoblin.media_types.ascii]]``.

Run

.. code-block:: bash

    ./bin/gmg dbupdate

Now any .txt file you uploaded will be processed as ascii art!


STL / 3d model support
======================

To enable the "STL" 3d model support plugin, first make sure you have
a recentish `Blender <http://blender.org>`_ installed and available on
your execution path.  This feature has been tested with Blender 2.63.
It may work on some earlier versions, but that is not guaranteed (and
is surely not to work prior to Blender 2.5X).

Add ``[[mediagoblin.media_types.stl]]`` under the ``[plugins]`` section in your
``mediagoblin_local.ini`` and restart MediaGoblin. 

Run

.. code-block:: bash

    ./bin/gmg dbupdate

You should now be able to upload .obj and .stl files and MediaGoblin
will be able to present them to your wide audience of admirers!

PDF and Document
================

To enable the "PDF and Document" support plugin, you need:

1. pdftocairo and pdfinfo for pdf only support.

2. unoconv with headless support to support converting libreoffice supported
   documents as well, such as doc/ppt/xls/odf/odg/odp and more.
   For the full list see mediagoblin/media_types/pdf/processing.py,
   unoconv_supported.

All executables must be on your execution path.

To install this on Fedora:

.. code-block:: bash

    sudo yum install -y poppler-utils unoconv libreoffice-headless

Note: You can leave out unoconv and libreoffice-headless if you want only pdf
support. This will result in a much smaller list of dependencies.

pdf.js relies on git submodules, so be sure you have fetched them:

.. code-block:: bash

    git submodule init
    git submodule update

This feature has been tested on Fedora with:
 poppler-utils-0.20.2-9.fc18.x86_64
 unoconv-0.5-2.fc18.noarch
 libreoffice-headless-3.6.5.2-8.fc18.x86_64

It may work on some earlier versions, but that is not guaranteed.

Add ``[[mediagoblin.media_types.pdf]]`` under the ``[plugins]`` section in your
``mediagoblin_local.ini`` and restart MediaGoblin. 

Run

.. code-block:: bash

    ./bin/gmg dbupdate


