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

We try to provide a nice theme for MediaGoblin by default, but of
course, you might want something different!  Maybe you want something
more light and colorful, or maybe you want something specifically
tailored to your organization.  Have no fear---MediaGoblin has theming
support!  This guide should walk you through installing and making
themes.


Installing a theme
==================

.. _theming-installing-section:

Installing the archive
----------------------

Say you have a theme archive such as ``goblincities.tar.gz`` and you
want to install this theme!  Don't worry, it's fairly painless.

1. ``cd ./user_dev/themes/``

2. Move the theme archive into this directory

3. ``tar -xzvf <tar-archive>``

4. Open your configuration file (probably named
   ``mediagoblin_local.ini``) and set the theme name::

       [mediagoblin]
       # ...
       theme = goblincities

5. Link the assets so that they can be served by your web server::

       $ ./bin/gmg assetlink

.. Note::

   If you ever change the current theme in your config file, you
   should re-run the above command!

(In the near future this should be even easier ;))

.. In the future, this might look more like:
.. Installing a theme in MediaGoblin is fairly easy!  Assuming you
.. already have a theme package, just do this::
..
..     $ ./bin/gmg theme install --fullsetup goblincities.tar.gz
..
.. This would install the theme, set it as current, and symlink its
.. assets.


Set up your webserver to serve theme assets
-------------------------------------------

If you followed the nginx setup example in :ref:`webserver-config` you
should already have theme asset setup.  However, if you set up your
server config with an older version of mediagoblin and the mediagoblin
docs, it's possible you don't have the "theme static files" alias, so
double check to make sure that section is there if you are having
problems.

If you are simply using this for local development and serving the
whole thing via paste/lazyserver, assuming you don't have a
paste_local.ini, the asset serving should be done for you.


Configuring where things go
---------------------------

By default, MediaGoblin's install directory for themes is
``./user_dev/themes/`` (relative to the MediaGoblin checkout or base
config file.)  However, you can change this location easily with the
``theme_install_dir`` setting in the ``[mediagoblin]`` section.

For example::

    [mediagoblin]
    # ... other parameters go here ...
    theme_install_dir = /path/to/themes/

Other variables you may consider setting:

`theme_web_path`
    When theme-specific assets are specified, this is where MediaGoblin
    will set the urls.  By default this is ``"/theme_static/"`` so in
    the case that your theme was trying to access its file 
    ``"images/shiny_button.png"`` MediaGoblin would link
    to ``/theme_static/images/shiny_button.png``.

`theme_linked_assets_dir`
    Your web server needs to serve the theme files out of some directory,
    and MediaGoblin will symlink the current theme's assets here.  See
    the "Link the assets" step in :ref:`theming-installing-section`.


Making a theme
==============

Okay, so a theme layout is pretty simple.  Let's assume we're making a
theme for an instance about hedgehogs!  We'll call this the
"hedgehogified" theme.

Change to where your ``theme_install_dir`` is set to (by default,
``./user_dev/themes/`` ... make those directories or otherwise adjust
if necessary)::

    hedgehogified/
    |- theme.cfg                # configuration file for this theme
    |- templates/               # override templates
    |  '- mediagoblin/
    |     |- base.html          # overriding mediagoblin/base.html
    |     '- root.html          # overriding mediagoblin/root.html
    '- assets/
    |  '- images/
    |  |  |- im_a_hedgehog.png  # hedgehog-containing image used by theme
    |  |  '- custom_logo.png    # your theme's custom logo
    |  '- css/
    |     '- hedgehog.css       # your site's hedgehog-specific css
    |- README.txt               # Optionally, a readme file (not required)
    |- AGPLv3.txt               # AGPL license file for your theme. (good practice)
    '- CC0_1.0.txt              # CC0 1.0 legalcode for the assets [if appropriate!]


The top level directory of your theme should be the symbolic name for
your theme.  This is the name that users will use to refer to activate
your theme.

.. Note::

   It's important to note that templates based on MediaGoblin's code
   should be released as AGPLv3 (or later), like MediaGoblin's code
   itself.  However, all the rest of your assets are up to you.  In this
   case, we are waiving our copyright for images and CSS into the public
   domain via CC0 (as MediaGoblin does) but do what's appropriate to you.


The config file
===============

The config file is not presently strictly required, though it is nice to have.
Only a few things need to go in here::

    [theme]
    name = Hedgehog-ification
    description = For hedgehog lovers ONLY
    licensing = AGPLv3 or later templates; assets (images/css) waived under CC0 1.0

The name and description fields here are to give users an idea of what
your theme is about.  For the moment, we don't have any listing
directories or admin interface, so this probably isn't useful, but
feel free to set it in anticipation of a more glorious future.

Licensing field is likewise a textual description of the stuff here;
it's recommended that you preserve the "AGPLv3 or later templates" and
specify whatever is appropriate to your assets.


Templates
---------

Your template directory is where you can put any override and custom
templates for MediaGoblin.

These follow the general MediaGoblin theming layout, which means that
the MediaGoblin core templates are all kept under the ``./mediagoblin/``
prefix directory.

You can copy files right out of MediaGoblin core and modify them in
this matter if you wish.

To fit with best licensing form, you should either preserve the
MediaGoblin copyright header borrowing from a MediaGoblin template, or
you may include one like the following::

    {#
    # [YOUR THEME], a MediaGoblin theme
    # Copyright (C) [YEAR] [YOUR NAME]
    #
    # This program is free software: you can redistribute it and/or modify
    # it under the terms of the GNU Affero General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.
    #
    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU Affero General Public License for more details.
    #
    # You should have received a copy of the GNU Affero General Public License
    # along with this program.  If not, see <http://www.gnu.org/licenses/>.
    #}


Assets
------

Put any files, such as images, CSS, etc, that are specific to your
theme in here.

You can reference these in your templates like so::

    <img src="{{ request.staticdirect('/images/im_a_shark.png', 'theme') }}" />

This will tell MediaGoblin to reference this image from the current theme.


Licensing file(s)
-----------------

You should include AGPLv3.txt with your theme as this is required for
the assets.  You can copy this from ``mediagoblin/licenses/``.

In the above example, we also use CC0 to waive our copyrights to
images and css, so we also included CC0_1.0.txt


A README.txt file
-----------------

A README file is not strictly required, but probably a good idea.  You
can put whatever in here, but restating the license choice clearly is
probably a good idea.


Simple theming by adding CSS
----------------------------

Many themes won't require anything other than the ability to override
some of MediaGoblin's core css.  Thankfully, doing so is easy if you
combine the above steps!

In your theme, do the following (make sure you make the necessary
directories and cd to your theme's directory first)::

    $ cp /path/to/mediagoblin/mediagoblin/templates/mediagoblin/extra_head.html templates/mediagoblin/

Great, now open that file and add something like this at the end::

    <link rel="stylesheet" type="text/css"
          href="{{ request.staticdirect('/css/theme.css', 'theme') }}"/>

You can name the css file whatever you like.  Now make the directory
for ``assets/css/`` and add the file ``assets/css/theme.css``.

You can now put custom CSS files in here and any CSS you add will
override default MediaGoblin CSS.


Packaging it up!
----------------

Packaging a theme is really easy.  It's just a matter of making an archive!

Change to the installed themes directory and run the following::

    tar -cvfz yourtheme.tar.gz yourtheme

Where "yourtheme" is replaced with your theme name.

That's it!
