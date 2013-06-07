.. MediaGoblin Documentation

   Written in 2013 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

==============================
Writing unit tests for plugins
==============================

Here's a brief guide to writing unit tests for plugins.  However, it
isn't really ideal.  It also hasn't been well tested... yes, there's
some irony there :)

Some notes: we're using py.test and webtest for unit testing stuff.
Keep that in mind.

My suggestion is to mime the behavior of `mediagoblin/tests/` and put
that in your own plugin, like `myplugin/tests/`.  Copy over
`conftest.py` and `pytest.ini` to your tests directory, but possibly
change the `test_app` fixture to match your own tests' config needs.
For example::

  import pkg_resources
  # [...]

  @pytest.fixture()
  def test_app(request):
      return get_app(
          request,
          mgoblin_config=pkg_resources.resource_filename(
              'myplugin.tests', 'myplugin_mediagoblin.ini'))

In any test module in your tests directory you can then do::

  def test_somethingorother(test_app):
      # real code goes here
      pass

And you'll get a mediagoblin application wrapped in webtest passed in
to your environment.

If your plugin needs to define multiple configuration setups, you can
actually set up multiple fixtures very easily for this.  You can just
set up multiple fixtures with different names that point to different
configs and pass them in as that named argument.

To run the tests, from mediagoblin's directory (make sure that your
plugin has been added to your mediagoblin checkout's virtualenv!) do::

  ./runtests.sh /path/to/myplugin/tests/

replacing `/path/to/myplugin/` with the actual path to your plugin.

NOTE: again, the above is untested, but it should probably work.  If
you run into trouble, `contact us
<http://mediagoblin.org/pages/join.html>`_, preferably on IRC!
