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


from mediagoblin.tests.tools import setup_fresh_app
from mediagoblin import mg_globals


DATA_TO_CACHE = {
    'herp': 'derp',
    'lol': 'cats'}


def _get_some_data(key):
    """
    Stuid function that makes use of some caching.
    """
    some_data_cache = mg_globals.cache.get_cache('sum_data')
    if some_data_cache.has_key(key):
        return some_data_cache.get(key)

    value = DATA_TO_CACHE.get(key)
    some_data_cache.put(key, value)
    return value


@setup_fresh_app
def test_cache_working(test_app):
    some_data_cache = mg_globals.cache.get_cache('sum_data')
    assert not some_data_cache.has_key('herp')
    assert _get_some_data('herp') == 'derp'
    assert some_data_cache.get('herp') == 'derp'
    # should get the same value again
    assert _get_some_data('herp') == 'derp'

    # now we force-change it, but the function should use the cached
    # version
    some_data_cache.put('herp', 'pred')
    assert _get_some_data('herp') == 'pred'
