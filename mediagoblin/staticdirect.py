# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

import pkg_resources
import logging

_log = logging.getLogger(__name__)


class StaticDirect(object):
    def __init__(self):
        self.cache = {}

    def __call__(self, filepath):
        if filepath in self.cache:
            return self.cache[filepath]

        if not pkg_resources.resource_exists('mediagoblin',
                'static' + filepath):
            _log.info("StaticDirect resource %r not found locally",
                filepath)
        static_direction = self.cache[filepath] = self.get(filepath)
        return static_direction

    def get(self, filepath):
        # should be implemented by the individual staticdirector
        pass


class RemoteStaticDirect(StaticDirect):
    def __init__(self, remotepath):
        StaticDirect.__init__(self)
        self.remotepath = remotepath.rstrip('/')

    def get(self, filepath):
        return '%s/%s' % (
            self.remotepath, filepath.lstrip('/'))


class MultiRemoteStaticDirect(StaticDirect):
    """
    For whene separate sections of the static data is served under
    separate urls.
    """
    def __init__(self, remotepaths):
        StaticDirect.__init__(self)
        self.remotepaths = remotepaths

    def get(self, filepath):
        section, rest = filepath.strip('/').split('/', 1)

        return '%s/%s' % (
            self.remotepaths[section].rstrip('/'),
            rest.lstrip('/'))
