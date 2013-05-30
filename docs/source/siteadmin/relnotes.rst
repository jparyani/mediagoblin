.. MediaGoblin Documentation

   Written in 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _release-notes:

=============
Release Notes
=============

This chapter has important information for releases in it.
If you're upgrading from a previous release, please read it
carefully, or at least skim over it.

0.4.0
=====

**Do this to upgrade**
1. Make sure to run ``bin/gmg dbupdate`` after upgrading.
2. See "For Theme authors" if you have a custom theme.
3. Note that ``./bin/gmg theme assetlink`` is now just
   ``./bin/gmg assetlink`` and covers both plugins and assets.
   Keep on reading to hear more about new plugin features.
4. If you want to take advantage of new plugins that have statically
   served assets, you are going to need to add the new "plugin_static"
   section to your nginx config.  Basically the following for nginx::

     # Plugin static files (usually symlinked in)
     location /plugin_static/ {
        alias /srv/mediagoblin.example.org/mediagoblin/user_dev/plugin_static/;
     }

**For theme authors**

If you have your own theme or you have any "user modified templates",
please note the following:

* mediagoblin/bits/ files above-content.html, body-end.html,
  body-start.html now are renamed... they have underscores instead of
  dashes in the filenames now :)
* There's a new file: ``mediagoblin/bits/frontpage_welcome.html``.
  You can easily customize this to give a welcome page appropriate to
  your site.

**New features**


0.3.3
=====

**Do this to upgrade**

1. Make sure to run ``bin/gmg dbupdate`` after upgrading.
2. OpenStreetMap is now a plugin, so if you want to use it, add the
   following to your config file:

   .. code-block:: ini

      [plugins]
      [[mediagoblin.plugins.geolocation]]

If you have your own theme, you may need to make some adjustments to
it as some theme related things may have changed in this release.  If
you run into problems, don't hesitate to
`contact us <http://mediagoblin.org/pages/join.html>`_
(IRC is often best).

**New features**

* New dropdown menu for accessing various features.

* Significantly improved URL generation.  Now mediagoblin won't give
  up on making a slug if it looks like there will be a duplicate;
  it'll try extra hard to generate a meaningful one instead.

  Similarly, linking to an id no longer can possibly conflict with
  linking to a slug; /u/username/m/id:35/ is the kind of reference we
  now use to linking to entries with ids.  However, old links with
  entries that linked to ids should work just fine with our migration.
  The only urls that might break in this release are ones using colons
  or equal signs.

* New template hooks for plugin authoring.

* As a demonstration of new template hooks for plugin authoring,
  openstreetmap support now moved to a plugin!

* Method to add media to collections switched from icon of paperclip
  to button with "add to collection" text.

* Bug where videos often failed to produce a proper thumbnail fixed!

* Copying around files in MediaGoblin now much more efficient, doesn't
  waste gobs of memory.

* Video transcoding now optional for videos that meet certain
  criteria.  By default, MediaGoblin will not transcode webm videos
  that are smaller in resolution than the MediaGoblin defaults, and
  MediaGoblin can also be configured to allow theora files to not be
  transcoded as well.

* Per-user license preference option; always want your uploads to be
  BY-SA and tired of changing that field?  You can now set your
  license preference in your user settings.

* Video player now responsive; better for mobile!

* You can now delete your account from the user preferences page if
  you so wish.

**Other changes**

* Plugin writers: Internal restructuring led to mediagoblin.db.sql* be
  mediagoblin.db.* starting from 0.3.3

* Dependency list has been reduced not requiring the "webob" package anymore.

* And many small fixes/improvements, too numerous to list!


0.3.2
=====

This will be the last release that is capable of converting from an earlier
MongoDB-based MediaGoblin instance to the newer SQL-based system.

**Do this to upgrade**

    # directory of your mediagoblin install
    cd /srv/mediagoblin.example.org

    # copy source for this release
    git fetch
    git checkout tags/v0.3.2

    # perform any needed database updates
    bin/gmg dbupdate
    
    # restart your servers however you do that, e.g.,
    sudo service mediagoblin-paster restart
    sudo service mediagoblin-celeryd restart


**New features**

* **3d model support!**

  You can now upload STL and OBJ files and display them in
  MediaGoblin.  Requires a recent-ish Blender; for details see:
  :ref:`deploying-chapter`

* **trim_whitespace**

  We bundle the optional plugin trim_whitespace which reduces the size
  of the delivered html output by reducing redundant whitespace.

  See :ref:`core-plugin-section` for plugin documentation

* **A new API!**

  It isn't well documented yet but we do have an API.  There is an
  `android application in progress <https://gitorious.org/mediagoblin/mediagoblin-android>`_
  which makes use of it, and there are some demo applications between
  `automgtic <https://github.com/jwandborg/automgtic>`_, an
  automatic media uploader for your desktop
  and `OMGMG <https://github.com/jwandborg/omgmg>`_, an example of
  a web application hooking up to the API.

  This is a plugin, so you have to enable it in your mediagoblin
  config file by adding a section under [plugins] like::

    [plugins]
    [[mediagoblin.plugins.api]]

  Note that the API works but is not nailed down... the way it is
  called may change in future releases.

* **OAuth login support**

  For applications that use OAuth to connect to the API.

  This is a plugin, so you have to enable it in your mediagoblin
  config file by adding a section under [plugins] like::

    [plugins]
    [[mediagoblin.plugins.oauth]]

* **Collections**

  We now have user-curated collections support.  These are arbitrary
  galleries that are customizable by users.  You can add media to
  these by clicking on the paperclip icon when logged in and looking
  at a media entry.

* **OpenStreetMap licensing display improvements**

  More accurate display of OSM licensing, and less disruptive: you
  click to "expand" the display of said licensing.

  Geolocation is also now on by default.

* **Miscelaneous visual improvements**

  We've made a number of small visual improvements including newer and
  nicer looking thumbnails and improved checkbox placement.



0.3.1
=====

**Do this to upgrade**

1. Make sure to run ``bin/gmg dbuptdate`` after upgrading.

2. If you set up your server config with an older version of
   mediagoblin and the mediagoblin docs, it's possible you don't
   have the "theme static files" alias, so double check to make
   sure that section is there if you are having problems.



**New features**

* **theming support**

  MediaGoblin now also includes theming support, which you can
  read about in the section :ref:`theming-chapter`.

* **flatpages**

  MediaGoblin has a flatpages plugin allowing you to add pages that
  are aren't media-related like "About this site...", "Terms of
  service...", etc.

  See :ref:`core-plugin-section` for plugin documentation


0.3.0
=====

This release has one important change. You need to act when
upgrading from a previous version!

This release changes the database system from MongoDB to
SQL(alchemy). If you want to setup a fresh instance, just
follow the instructions in the deployment chapter. If on
the other hand you want to continue to use one instance,
read on.

To convert your data from MongoDB to SQL(alchemy), you need
to follow these steps:

1. Make sure your MongoDB is still running and has your
   data, it's needed for the conversion.

2. Configure the ``sql_engine`` URI in the config to represent
   your target database (see: :ref:`deploying-chapter`)

3. You need an empty database.

4. Then run the following command::

       bin/gmg [-cf mediagoblin_config.ini] convert_mongo_to_sql

5. Start your server and investigate.

6. That's it.
