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
from __future__ import unicode_literals

import logging
from mediagoblin.tools.pluginapi import get_config
from mediagoblin.tools import licenses

__VERSION__ = '0.1.2' # releases get numbers, post release a "+" appended
_log = logging.getLogger(__name__)

SORTED_PLUGIN_LICENSES = []
"""This is the equivalent of MG.tools.licenses.SORTED_LICENSES
that we want to replace"""


class CustomLicenses(object):
    _setup_plugin_called = 0

    @classmethod
    def setup_plugin(cls):
        if cls._setup_plugin_called:
            return # Only set up once
        cls._setup_plugin_called += 1
        _log.info('Configurable license plugin setting up!')
        # Get configured licenses
        config = get_config(cls.__module__)
        if not config:
            _log.warn('There are no licenses configured at all.')
            return # Nothing configured, nothing to do...

        for k,v in config.iteritems():
            if not k.lower().startswith('license_'):
                continue
            (abbrev, name, url) =  config.as_list(k)
            _log.info("Adding license: {0}".format(abbrev))
            SORTED_PLUGIN_LICENSES.append(licenses.License(abbrev, name, url))

        # Set the regular license list to our custom ones:
        licenses.SORTED_LICENSES = SORTED_PLUGIN_LICENSES
        # create dict {url: License,...} to enable fast license lookup by url.

        # The data structure in
        # mediagoblin.tools.licenses.SUPPORTED_LICENSES and SORTED_LICENSES
        # is really not optimal. What we want there is a "OrderedDict" that
        # can give us order AND quick lookup by key at the same time. But as
        # that is python >=2.7 and we have to deal with python 2.6, we'll
        # live with the data duplication in 2 structures for now. It's not
        # like we are going to have hundreds of licenses, fortunately.
        licenses.SUPPORTED_LICENSES = dict(((l.uri, l) for l in \
                                                SORTED_PLUGIN_LICENSES))


hooks = {
    'setup': CustomLicenses.setup_plugin
    }
