.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _theming-chapter:

=====================
 Theming MediaGoblin
=====================

We try to provide a nice theme for MediaGoblin by default.  But of
course, you might want something different!  Maybe you want something
more light and colorful, or maybe you want something specifically
tailored to your organization.  Have no fear, MediaGoblin has theming
support!  This guide should walk you through installing and making themes.


Making a theme
--------------

The structure of things
=======================

Okay, so a theme layout is pretty simple.  Let's assume we're making a
theme for an instance about hedgehogs!  We'll call this the
"hedgehogified" theme.

    hedgehogified/
    |- theme.cfg                   # configuration file for this theme
    |- templates/                  # override templates
    |  '- mediagoblin/
    |     |- base.html             # overriding mediagoblin/base.html
    |     '- root.html             # overriding mediagoblin/root.html
    '- assets/
    |  '- images/
    |  |  |- im_a_hedgehog.png     # hedgehog-containing image used by theme
    |  |  '- custom_logo.png       # your theme's custom logo
    |  '- css/
    |     '- hedgehog.css          # your site's hedgehog-specific css
    |- README.txt                  # Optionally, a readme file (not required)
    |- AGPLv3.txt                  # AGPL license file for your theme. (good practice)
    '- CC0.txt                     # CC0 1.0 legalcode for the assets [if appropriate!]

The top level directory of your theme should be the symbolic name for
your theme.  This is the name that users will use to refer to activate
your theme.

It's important to note that templates based on MediaGoblin's code
should be released as AGPLv3 (or later), like MediaGoblin's code
itself.  However, all the rest of your assets are up to you.  In this
case, we are waiving our copyright for images and CSS into the public
domain via CC0 (as MediaGoblin does) but do what's appropriate to you.

The config file
~~~~~~~~~~~~~~~

Only a few things need to go in here.

   [theme]
   name = hedgehogified
   description = For hedgehog lovers ONLY
   licensing = AGPLv3 or later templates; assets (images/css) waived under CC0 1.0


Templates
~~~~~~~~~

Templates

Licensing file(s)
~~~~~~~~~~~~~~~~~




A README.txt file
~~~~~~~~~~~~~~~~~

A readme file is not strictly required, but probably a good idea.


Referring to custom assets in your themes
=========================================




Installing a theme
------------------

Installing a theme in MediaGoblin is fairly easy!  Assuming you
already have a theme package, just do this:

  $ ./bin/gmg theme install --fullsetup goblincities.tar.gz

This installs, archives, and 


Making a themes
---------------


