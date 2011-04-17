# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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


import logging
import os


MAKE_SUBDIRECTORIES = ['media/queue', 'media/public', 'beaker']


class MakeUserDevDirs(object):
    """
    Simple recipe for making subdirectories for user buildout convenience
    """
    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options

        if self.options['path'].startswith('/'):
            self.path = self.options['path']
        else:
            self.path = os.path.join(
                self.buildout['buildout']['directory'],
                self.options['path'])

    def install(self):
        for make_subdir in MAKE_SUBDIRECTORIES:
            fulldir = os.path.join(self.path, make_subdir)

            if not os.path.exists(fulldir):
                logging.getLogger(self.name).info(
                    'Creating directory %s' % fulldir)
                os.makedirs(fulldir)

        return ()

    update = install
