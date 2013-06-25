.. MediaGoblin Documentation

   Written in 2013 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _plugin-api-chapter:

==========
Plugin API
==========

This documents the general plugin API.

Please note, at this point OUR PLUGIN HOOKS MAY AND WILL CHANGE.
Authors are encouraged to develop plugins and work with the
MediaGoblin community to keep them up to date, but this API will be a
moving target for a few releases.

Please check the :ref:`release-notes` for updates!


How are hooks added?  Where do I find them?
-------------------------------------------

Much of this document talks about hooks, both as in terms of regular
hooks and template hooks.  But where do they come from, and how can
you find a list of them?

For the moment, the best way to find available hooks is to check the
source code itself.  (Yes, we should start a more official hook
listing with descriptions soon.)  But many hooks you may need do not
exist yet: what to do then?

The plan at present is that we are adding hooks as people need them,
with community discussion.  If you find that you need a hook and
MediaGoblin at present doesn't provide it at present, please
`http://mediagoblin.org/pages/join.html <talk to us>`_!  We'll
evaluate what to do from there.


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

You can access this via the app_config variables in mg_globals, or you
can use a shortcut to get your plugin's config section::

  >>> from mediagoblin.tools import pluginapi
  # Replace with the path to your plugin.
  # (If an external package,  it won't be part of mediagoblin.plugins)
  >>> floobie_config = pluginapi.get_config('mediagoblin.plugins.floobifier')
  >>> floobie_dir = floobie_config['floobie_dir']
  # This is the same as the above
  >>> from mediagoblin import mg_globals
  >>> config = mg_globals.global_config['plugins']['mediagoblin.plugins.floobifier']
  >>> floobie_dir = floobie_config['floobie_dir']
  
A tip: you have access to the `%(here)s` variable in your config,
which is the directory that the user's mediagoblin config is running
out of.  So for example, your plugin may need a "floobie" directory to
store floobs in.  You could give them a reasonable default that makes
use of the default `user_dev` location, but allow users to override
it, like so::

  [plugin_spec]
  floobie_dir = string(default="%(here)s/user_dev/floobs/")

Note, this is relative to the user's mediagoblin config directory,
*not* your plugin directory!


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


Adding static resources
-----------------------

It's possible to add static resources for your plugin.  Say your
plugin needs some special javascript and images... how to provide
them?  Then how to access them?  MediaGoblin has a way!


Attaching to the hook
+++++++++++++++++++++

First, you need to register your plugin's resources with the hook.
This is pretty easy actually: you just need to provide a function that
passes back a PluginStatic object.

.. autoclass:: mediagoblin.tools.staticdirect.PluginStatic


Running plugin assetlink
++++++++++++++++++++++++

In order for your plugin assets to be properly served by MediaGoblin,
your plugin's asset directory needs to be symlinked into the directory
that plugin assets are served from.  To set this up, run::

  ./bin/gmg assetlink


Using staticdirect
++++++++++++++++++

Once you have this, you will want to be able to of course link to your
assets!  MediaGoblin has a "staticdirect" tool; you want to use this
like so in your templates::

  staticdirect("css/monkeys.css", "mystaticname")

Replace "mystaticname" with the name you passed to PluginStatic.  The
staticdirect method is, for convenience, attached to the request
object, so you can access this in your templates like:

.. code-block:: html

  <img alt="A funny bunny"
       src="{{ request.staticdirect('images/funnybunny.png', 'mystaticname') }}" />


Additional hook tips
--------------------

This section aims to explain some tips in regards to adding hooks to
the MediaGoblin repository.

WTForms hooks
+++++++++++++

We haven't totally settled on a way to tranform wtforms form objects,
but here's one way.  In your view::

  from mediagoblin.foo.forms import SomeForm

  def some_view(request)
      form_class = hook_transform('some_form_transform', SomeForm)
      form = form_class(request.form)

Then to hook into this form, do something in your plugin like::

  import wtforms

  class SomeFormAdditions(wtforms.Form):
      new_datefield = wtforms.DateField()

  def transform_some_form(orig_form):
      class ModifiedForm(orig_form, SomeFormAdditions)
      return ModifiedForm

  hooks = {
      'some_form_transform': transform_some_form}


Interfaces
++++++++++

If you want to add a pseudo-interface, it's not difficult to do so.
Just write the interface like so::

  class FrobInterface(object):
      """
      Interface for Frobbing.

      Classes implementing this interface should provide defrob and frob.
      They may also implement double_frob, but it is not required; if
      not provided, we will use a general technique.
      """

      def defrob(self, frobbed_obj):
          """
          Take a frobbed_obj and defrob it.  Returns the defrobbed object.
          """
          raise NotImplementedError()
      
      def frob(self, normal_obj):
          """
          Take a normal object and frob it.  Returns the frobbed object.
          """
          raise NotImplementedError()

      def double_frob(self, normal_obj):
          """
          Frob this object and return it multiplied by two.
          """
          return self.frob(normal_obj) * 2


  def some_frob_using_method():
      # something something something
      frobber = hook_handle(FrobInterface)
      frobber.frob(blah)

      # alternately you could have a default
      frobber = hook_handle(FrobInterface) or DefaultFrobber
      frobber.defrob(foo)


It's fine to use your interface as the key instead of a string if you
like.  (Usually this is messy, but since interfaces are public and
since you need to import them into your plugin anyway, interfaces
might as well be keys.)

Then a plugin providing your interface can be like::

  from mediagoblin.foo.frobfrogs import FrobInterface
  from frogfrobber import utils

  class FrogFrobber(FrobInterface):
      """
      Takes a frogputer science approach to frobbing.
      """
      def defrob(self, frobbed_obj):
          return utils.frog_defrob(frobbed_obj)

      def frob(self, normal_obj):
          return utils.frog_frob(normal_obj)

   hooks = {
       FrobInterface: lambda: return FrogFrobber}
