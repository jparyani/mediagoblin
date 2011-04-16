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


import os
import tempfile

from nose.tools import assert_raises
from werkzeug.utils import secure_filename

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
    tmpdir, this_storage = get_tmp_filestorage()

    os.makedirs(os.path.join(tmpdir, 'dir1', 'dir2'))
    filename = os.path.join(tmpdir, 'dir1', 'dir2', 'filename.txt')
    with open(filename, 'w') as ourfile:
        ourfile.write("I'm having a lovely day!")

    assert this_storage.file_exists(['dir1', 'dir2', 'filename.txt'])
    assert not this_storage.file_exists(['dir1', 'dir2', 'thisfile.lol'])
    assert not this_storage.file_exists(['dnedir1', 'dnedir2', 'somefile.lol'])


def test_basic_storage_get_unique_filepath():
    tmpdir, this_storage = get_tmp_filestorage()
    
    # write something that exists
    os.makedirs(os.path.join(tmpdir, 'dir1', 'dir2'))
    filename = os.path.join(tmpdir, 'dir1', 'dir2', 'filename.txt')
    with open(filename, 'w') as ourfile:
        ourfile.write("I'm having a lovely day!")

    # now we want something new, with the same name!
    new_filepath = this_storage.get_unique_filepath(
        ['dir1', 'dir2', 'filename.txt'])
    assert new_filepath[:-1] == [u'dir1', u'dir2']

    new_filename = new_filepath[-1]
    assert new_filename.endswith('filename.txt')
    assert len(new_filename) > len('filename.txt')
    assert new_filename == secure_filename(new_filename)


def test_basic_storage_get_file():
    tmpdir, this_storage = get_tmp_filestorage()

    # Write a brand new file
    filepath = ['dir1', 'dir2', 'ourfile.txt']

    with this_storage.get_file(filepath, 'w') as our_file:
        our_file.write('First file')
    with this_storage.get_file(filepath, 'r') as our_file:
        assert our_file.read() == 'First file'
    assert os.path.exists(os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'))
    with file(os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'), 'r') as our_file:
        assert our_file.read() == 'First file'

    # Write to the same path but try to get a unique file.
    new_filepath = this_storage.get_unique_filepath(filepath)
    assert not os.path.exists(os.path.join(tmpdir, *new_filepath))

    with this_storage.get_file(new_filepath, 'w') as our_file:
        our_file.write('Second file')
    with this_storage.get_file(new_filepath, 'r') as our_file:
        assert our_file.read() == 'Second file'
    assert os.path.exists(os.path.join(tmpdir, *new_filepath))
    with file(os.path.join(tmpdir, *new_filepath), 'r') as our_file:
        assert our_file.read() == 'Second file'

    # Read from an existing file
    manually_written_file = os.makedirs(
        os.path.join(tmpdir, 'testydir'))
    with file(os.path.join(tmpdir, 'testydir/testyfile.txt'), 'w') as testyfile:
        testyfile.write('testy file!  so testy.')

    with this_storage.get_file(['testydir', 'testyfile.txt']) as testyfile:
        assert testyfile.read() == 'testy file!  so testy.'


def test_basic_storage_delete_file():
    tmpdir, this_storage = get_tmp_filestorage()

    assert not os.path.exists(
        os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'))

    filepath = ['dir1', 'dir2', 'ourfile.txt']
    with this_storage.get_file(filepath, 'w') as our_file:
        our_file.write('Testing this file')

    assert os.path.exists(
        os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'))

    this_storage.delete_file(filepath)
    
    assert not os.path.exists(
        os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'))


def test_basic_storage_url_for_file():
    pass
