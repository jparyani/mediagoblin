# GNU Mediagoblin -- federated, autonomous media hosting
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


from mediagoblin import storage


def test_clean_listy_filepath():
    expected = [u'dir1', u'dir2', u'linooks.jpg']
    assert storage.clean_listy_filepath(
        ['dir1', 'dir2', 'linooks.jpg']) == expected

    expected = [u'dir1', u'foo_.._nasty', u'linooks.jpg']
    assert storage.clean_listy_filepath(
        ['/dir1/', 'foo/../nasty', 'linooks.jpg']) == expected

    expected = [u'etc', u'passwd']
    assert storage.clean_listy_filepath(
        ['../../../etc/', 'passwd']) == expected
