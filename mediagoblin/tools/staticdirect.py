# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
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

####################################
# Staticdirect infrastructure.
# Borrowed largely from cc.engine
# by Chris Webber & Creative Commons
#
# This needs documentation!
####################################

import logging

_log = logging.getLogger(__name__)


class StaticDirect(object):
    """
    Direct to a static resource.

    This StaticDirect class can take a series of "domains" to
    staticdirect to.  In general, you should supply a None domain, as
    that's the "default" domain.

    Things work like this:
      >>> staticdirect = StaticDirect(
      ...     {None: "/static/",
      ...      "theme": "http://example.org/themestatic/"})
      >>> staticdirect("css/monkeys.css")
      "/static/css/monkeys.css"
      >>> staticdirect("images/lollerskate.png", "theme")
      "http://example.org/themestatic/images/lollerskate.png"
    """
    def __init__(self, domains):
        self.domains = dict(
            [(key, value.rstrip('/'))
             for key, value in domains.iteritems()])
        self.cache = {}

    def __call__(self, filepath, domain=None):
        if domain in self.cache and filepath in self.cache[domain]:
            return self.cache[domain][filepath]

        static_direction = self.cache.setdefault(
            domain, {})[filepath] = self.get(filepath, domain)
        return static_direction

    def get(self, filepath, domain=None):
        return '%s/%s' % (
            self.domains[domain], filepath.lstrip('/'))


class PluginStatic(object):
    """Pass this into the ``'static_setup'`` hook to register your
    plugin's static directory.

    This has two mandatory attributes that you must pass in on class
    init:
     - name: this name will be both used for lookup in "urlgen" for
       your plugin's static resources and for the subdirectory that
       it'll be "mounted" to for serving via your web browser.  It
       *MUST* be unique.  If writing a plugin bundled with MediaGoblin
       please use the pattern 'coreplugin__foo' where 'foo' is your
       plugin name.  All external plugins should use their modulename,
       so if your plugin is 'mg_bettertags' you should also call this
       name 'mg_bettertags'.
     - file_path: the directory your plugin's static resources are
       located in.  It's recommended that you use
       pkg_resources.resource_filename() for this.

    An example of using this::

      from pkg_resources import resource_filename
      from mediagoblin.tools.staticdirect import PluginStatic

      hooks = {
          'static_setup': lambda: PluginStatic(
              'mg_bettertags',
              resource_filename('mg_bettertags', 'static'))
      }

    """
    def __init__(self, name, file_path):
        self.name = name
        self.file_path = file_path

    def __call__(self):
        return self
