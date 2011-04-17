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

from mediagoblin import util


def _import_component_testing_method(silly_string):
    # Just for the sake of testing that our component importer works.
    return u"'%s' is the silliest string I've ever seen" % silly_string


def test_import_component():
    imported_func = util.import_component(
        'mediagoblin.tests.test_util:_import_component_testing_method')
    result = imported_func('hooobaladoobala')
    expected = u"'hooobaladoobala' is the silliest string I've ever seen"
    assert result == expected
