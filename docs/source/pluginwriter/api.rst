.. MediaGoblin Documentation

   Written in 2013 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.


==========
Plugin API
==========

This documents the general plugin API.

Please note, at this point OUR PLUGIN HOOKS MAY AND WILL CHANGE.
Authors are encouraged to develop plugins and work with the
MediaGoblin community to keep them up to date, but this API will be a
moving target for a few releases.

Please check the release notes for updates!

:mod:`pluginapi` Module
-----------------------

.. automodule:: mediagoblin.tools.pluginapi
   :members: get_config, register_routes, register_template_path,
             register_template_hooks, get_hook_templates,
             hook_handle, hook_runall, hook_transform

Configuration
-------------

Your plugin may define its own configuration defaults.

Simply add to the directory of your plugin a config_spec.ini file.  An
example might look like::

  [plugin_spec]
  some_string = string(default="blork")
  some_int = integer(default=50)

This means that when people enable your plugin in their config you'll
be able to provide defaults as well as type validation.


Context Hooks
-------------

View specific hooks
+++++++++++++++++++

You can hook up to almost any template called by any specific view
fairly easily.  As long as the view directly or indirectly uses the
method ``render_to_response`` you can access the context via a hook
that has a key in the format of the tuple::

  (view_symbolic_name, view_template_path)

Where the "view symbolic name" is the same parameter used in
``request.urlgen()`` to look up the view.  So say we're wanting to add
something to the context of the user's homepage.  We look in
mediagoblin/user_pages/routing.py and see::

  add_route('mediagoblin.user_pages.user_home',
            '/u/<string:user>/',
            'mediagoblin.user_pages.views:user_home')

Aha!  That means that the name is ``mediagoblin.user_pages.user_home``.
Okay, so then we look at the view at the
``mediagoblin.user_pages.user_home`` method::

  @uses_pagination
  def user_home(request, page):
      # [...] whole bunch of stuff here
      return render_to_response(
          request,
          'mediagoblin/user_pages/user.html',
          {'user': user,
           'user_gallery_url': user_gallery_url,
           'media_entries': media_entries,
           'pagination': pagination})

Nice!  So the template appears to be
``mediagoblin/user_pages/user.html``.  Cool, that means that the key
is::

  ("mediagoblin.user_pages.user_home",
   "mediagoblin/user_pages/user.html")

The context hook uses ``hook_transform()`` so that means that if we're
hooking into it, our hook will both accept one argument, ``context``,
and should return that modified object, like so::

  def add_to_user_home_context(context):
      context['foo'] = 'bar'
      return context
  
  hooks = {
      ("mediagoblin.user_pages.user_home",
       "mediagoblin/user_pages/user.html"): add_to_user_home_context}


Global context hooks
++++++++++++++++++++

If you need to add something to the context of *every* view, it is not
hard; there are two hooks hook that also uses hook_transform (like the
above) but make available what you are providing to *every* view.

Note that there is a slight, but critical, difference between the two.

The most general one is the ``'template_global_context'`` hook.  This
one is run only once, and is read into the global context... all views
will get access to what are in this dict.

The slightly more expensive but more powerful one is
``'template_context_prerender'``.  This one is not added to the global
context... it is added to the actual context of each individual
template render right before it is run!  Because of this you also can
do some powerful and crazy things, such as checking the request object
or other parts of the context before passing them on.
