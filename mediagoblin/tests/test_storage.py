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


import os
import tempfile

from nose.tools import assert_raises

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

    assert_raises(
        storage.InvalidFilepath,
        storage.clean_listy_filepath,
        ['../../', 'linooks.jpg'])


##########################
# Basic file storage tests
##########################

def get_tmp_filestorage(mount_url=None):
    tmpdir = tempfile.mkdtemp()
    this_storage = storage.BasicFileStorage(tmpdir, mount_url)
    return tmpdir, this_storage


def test_basic_storage__resolve_filepath():
    tmpdir, this_storage = get_tmp_filestorage()

    result = this_storage._resolve_filepath(['dir1', 'dir2', 'filename.jpg'])
    assert result == os.path.join(
        tmpdir, 'dir1/dir2/filename.jpg')

    result = this_storage._resolve_filepath(['../../etc/', 'passwd'])
    assert result == os.path.join(
        tmpdir, 'etc/passwd')

    assert_raises(
        storage.InvalidFilepath,
        this_storage._resolve_filepath,
        ['../../', 'etc', 'passwd'])


def test_basic_storage_file_exists():
    pass


def test_basic_storage_get_file():
    pass


def test_basic_storage_delete_file():
    pass


def test_basic_storage_url_for_file():
    pass
