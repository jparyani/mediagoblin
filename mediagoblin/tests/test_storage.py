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


import os
import tempfile

import pytest
import six

from werkzeug.utils import secure_filename

from mediagoblin import storage


################
# Test utilities
################

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

    with pytest.raises(storage.InvalidFilepath):
        storage.clean_listy_filepath(['../../', 'linooks.jpg'])


class FakeStorageSystem(object):
    def __init__(self, foobie, blech, **kwargs):
        self.foobie = foobie
        self.blech = blech

class FakeRemoteStorage(storage.filestorage.BasicFileStorage):
    # Theoretically despite this, all the methods should work but it
    # should force copying to the workbench
    local_storage = False

    def copy_local_to_storage(self, *args, **kwargs):
        return storage.StorageInterface.copy_local_to_storage(
            self, *args, **kwargs)


def test_storage_system_from_config():
    this_storage = storage.storage_system_from_config(
        {'base_url': 'http://example.org/moodia/',
         'base_dir': '/tmp/',
         'garbage_arg': 'garbage_arg',
         'garbage_arg': 'trash'})
    assert this_storage.base_url == 'http://example.org/moodia/'
    assert this_storage.base_dir == '/tmp/'
    assert this_storage.__class__ is storage.filestorage.BasicFileStorage

    this_storage = storage.storage_system_from_config(
        {'foobie': 'eiboof',
         'blech': 'hcelb',
         'garbage_arg': 'garbage_arg',
         'storage_class':
             'mediagoblin.tests.test_storage:FakeStorageSystem'})
    assert this_storage.foobie == 'eiboof'
    assert this_storage.blech == 'hcelb'
    assert six.text_type(this_storage.__class__) == \
        u"<class 'mediagoblin.tests.test_storage.FakeStorageSystem'>"


##########################
# Basic file storage tests
##########################

def get_tmp_filestorage(mount_url=None, fake_remote=False):
    tmpdir = tempfile.mkdtemp(prefix="test_gmg_storage")
    if fake_remote:
        this_storage = FakeRemoteStorage(tmpdir, mount_url)
    else:
        this_storage = storage.filestorage.BasicFileStorage(tmpdir, mount_url)
    return tmpdir, this_storage


def cleanup_storage(this_storage, tmpdir, *paths):
    for p in paths:
        while p:
            assert this_storage.delete_dir(p) == True
            p.pop(-1)
    os.rmdir(tmpdir)


def test_basic_storage__resolve_filepath():
    tmpdir, this_storage = get_tmp_filestorage()

    result = this_storage._resolve_filepath(['dir1', 'dir2', 'filename.jpg'])
    assert result == os.path.join(
        tmpdir, 'dir1/dir2/filename.jpg')

    result = this_storage._resolve_filepath(['../../etc/', 'passwd'])
    assert result == os.path.join(
        tmpdir, 'etc/passwd')

    pytest.raises(
        storage.InvalidFilepath,
        this_storage._resolve_filepath,
        ['../../', 'etc', 'passwd'])

    cleanup_storage(this_storage, tmpdir)


def test_basic_storage_file_exists():
    tmpdir, this_storage = get_tmp_filestorage()

    os.makedirs(os.path.join(tmpdir, 'dir1', 'dir2'))
    filename = os.path.join(tmpdir, 'dir1', 'dir2', 'filename.txt')
    with open(filename, 'w') as ourfile:
        ourfile.write("I'm having a lovely day!")

    assert this_storage.file_exists(['dir1', 'dir2', 'filename.txt'])
    assert not this_storage.file_exists(['dir1', 'dir2', 'thisfile.lol'])
    assert not this_storage.file_exists(['dnedir1', 'dnedir2', 'somefile.lol'])

    this_storage.delete_file(['dir1', 'dir2', 'filename.txt'])
    cleanup_storage(this_storage, tmpdir, ['dir1', 'dir2'])


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

    os.remove(filename)
    cleanup_storage(this_storage, tmpdir, ['dir1', 'dir2'])


def test_basic_storage_get_file():
    tmpdir, this_storage = get_tmp_filestorage()

    # Write a brand new file
    filepath = ['dir1', 'dir2', 'ourfile.txt']

    with this_storage.get_file(filepath, 'w') as our_file:
        our_file.write('First file')
    with this_storage.get_file(filepath, 'r') as our_file:
        assert our_file.read() == 'First file'
    assert os.path.exists(os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'))
    with open(os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'), 'r') as our_file:
        assert our_file.read() == 'First file'

    # Write to the same path but try to get a unique file.
    new_filepath = this_storage.get_unique_filepath(filepath)
    assert not os.path.exists(os.path.join(tmpdir, *new_filepath))

    with this_storage.get_file(new_filepath, 'w') as our_file:
        our_file.write('Second file')
    with this_storage.get_file(new_filepath, 'r') as our_file:
        assert our_file.read() == 'Second file'
    assert os.path.exists(os.path.join(tmpdir, *new_filepath))
    with open(os.path.join(tmpdir, *new_filepath), 'r') as our_file:
        assert our_file.read() == 'Second file'

    # Read from an existing file
    manually_written_file = os.makedirs(
        os.path.join(tmpdir, 'testydir'))
    with open(os.path.join(tmpdir, 'testydir/testyfile.txt'), 'w') as testyfile:
        testyfile.write('testy file!  so testy.')

    with this_storage.get_file(['testydir', 'testyfile.txt']) as testyfile:
        assert testyfile.read() == 'testy file!  so testy.'

    this_storage.delete_file(filepath)
    this_storage.delete_file(new_filepath)
    this_storage.delete_file(['testydir', 'testyfile.txt'])
    cleanup_storage(this_storage, tmpdir, ['dir1', 'dir2'], ['testydir'])


def test_basic_storage_delete_file():
    tmpdir, this_storage = get_tmp_filestorage()

    assert not os.path.exists(
        os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'))

    filepath = ['dir1', 'dir2', 'ourfile.txt']
    with this_storage.get_file(filepath, 'w') as our_file:
        our_file.write('Testing this file')

    assert os.path.exists(
        os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'))

    assert this_storage.delete_dir(['dir1', 'dir2']) == False
    this_storage.delete_file(filepath)
    assert this_storage.delete_dir(['dir1', 'dir2']) == True
    
    assert not os.path.exists(
        os.path.join(tmpdir, 'dir1/dir2/ourfile.txt'))

    cleanup_storage(this_storage, tmpdir, ['dir1'])


def test_basic_storage_url_for_file():
    # Not supplying a base_url should actually just bork.
    tmpdir, this_storage = get_tmp_filestorage()
    pytest.raises(
        storage.NoWebServing,
        this_storage.file_url,
        ['dir1', 'dir2', 'filename.txt'])
    cleanup_storage(this_storage, tmpdir)

    # base_url without domain
    tmpdir, this_storage = get_tmp_filestorage('/media/')
    result = this_storage.file_url(
        ['dir1', 'dir2', 'filename.txt'])
    expected = '/media/dir1/dir2/filename.txt'
    assert result == expected
    cleanup_storage(this_storage, tmpdir)

    # base_url with domain
    tmpdir, this_storage = get_tmp_filestorage(
        'http://media.example.org/ourmedia/')
    result = this_storage.file_url(
        ['dir1', 'dir2', 'filename.txt'])
    expected = 'http://media.example.org/ourmedia/dir1/dir2/filename.txt'
    assert result == expected
    cleanup_storage(this_storage, tmpdir)


def test_basic_storage_get_local_path():
    tmpdir, this_storage = get_tmp_filestorage()
    
    result = this_storage.get_local_path(
        ['dir1', 'dir2', 'filename.txt'])

    expected = os.path.join(
        tmpdir, 'dir1/dir2/filename.txt')

    assert result == expected

    cleanup_storage(this_storage, tmpdir)


def test_basic_storage_is_local():
    tmpdir, this_storage = get_tmp_filestorage()
    assert this_storage.local_storage is True
    cleanup_storage(this_storage, tmpdir)


def test_basic_storage_copy_locally():
    tmpdir, this_storage = get_tmp_filestorage()

    dest_tmpdir = tempfile.mkdtemp()

    filepath = ['dir1', 'dir2', 'ourfile.txt']
    with this_storage.get_file(filepath, 'w') as our_file:
        our_file.write('Testing this file')

    new_file_dest = os.path.join(dest_tmpdir, 'file2.txt')

    this_storage.copy_locally(filepath, new_file_dest)
    this_storage.delete_file(filepath)
    
    assert open(new_file_dest).read() == 'Testing this file'

    os.remove(new_file_dest)
    os.rmdir(dest_tmpdir)
    cleanup_storage(this_storage, tmpdir, ['dir1', 'dir2'])


def _test_copy_local_to_storage_works(tmpdir, this_storage):
    local_filename = tempfile.mktemp()
    with open(local_filename, 'w') as tmpfile:
        tmpfile.write('haha')

    this_storage.copy_local_to_storage(
        local_filename, ['dir1', 'dir2', 'copiedto.txt'])

    os.remove(local_filename)

    assert open(
        os.path.join(tmpdir, 'dir1/dir2/copiedto.txt'),
        'r').read() == 'haha'

    this_storage.delete_file(['dir1', 'dir2', 'copiedto.txt'])
    cleanup_storage(this_storage, tmpdir, ['dir1', 'dir2'])


def test_basic_storage_copy_local_to_storage():
    tmpdir, this_storage = get_tmp_filestorage()
    _test_copy_local_to_storage_works(tmpdir, this_storage)


def test_general_storage_copy_local_to_storage():
    tmpdir, this_storage = get_tmp_filestorage(fake_remote=True)
    _test_copy_local_to_storage_works(tmpdir, this_storage)
