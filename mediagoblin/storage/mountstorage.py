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

from mediagoblin.storage import StorageInterface, clean_listy_filepath


class MountError(Exception):
    pass


class MountStorage(StorageInterface):
    """
    Experimental "Mount" virtual Storage Interface

    This isn't an interface to some real storage, instead it's a
    redirecting interface, that redirects requests to other
    "StorageInterface"s.

    For example, say you have the paths:

     1. ['user_data', 'cwebber', 'avatar.jpg']
     2. ['user_data', 'elrond', 'avatar.jpg']
     3. ['media_entries', '34352f304c3f4d0ad8ad0f043522b6f2', 'thumb.jpg']

    You could mount media_entries under CloudFileStorage and user_data
    under BasicFileStorage.  Then 1 would be passed to
    BasicFileStorage under the path ['cwebber', 'avatar.jpg'] and 3
    would be passed to CloudFileStorage under
    ['34352f304c3f4d0ad8ad0f043522b6f2', 'thumb.jpg'].

    In other words, this is kind of like mounting /home/ and /etc/
    under different filesystems on your operating system... but with
    mediagoblin filestorages :)

    To set this up, you currently need to call the mount() method with
    the target path and a backend, that shall be available under that
    target path.  You have to mount things in a sensible order,
    especially you can't mount ["a", "b"] before ["a"].
    """
    def __init__(self, **kwargs):
        self.mounttab = {}

    def mount(self, dirpath, backend):
        """
        Mount a new backend under dirpath
        """
        new_ent = clean_listy_filepath(dirpath)

        print "Mounting:", repr(new_ent)
        already, rem_1, table, rem_2 = self._resolve_to_backend(new_ent, True)
        print "===", repr(already), repr(rem_1), repr(rem_2), len(table)

        assert (len(rem_2) > 0) or (None not in table), \
            "That path is already mounted"
        assert (len(rem_2) > 0) or (len(table) == 0), \
            "A longer path is already mounted here"

        for part in rem_2:
            table[part] = {}
            table = table[part]
        table[None] = backend

    def _resolve_to_backend(self, filepath, extra_info=False):
        """
        extra_info = True is for internal use!

        Normally, returns the backend and the filepath inside that backend.

        With extra_info = True it returns the last directory node and the
        remaining filepath from there in addition.
        """
        table = self.mounttab
        filepath = filepath[:]
        res_fp = None
        while True:
            new_be = table.get(None)
            if (new_be is not None) or res_fp is None:
                res_be = new_be
                res_fp = filepath[:]
                res_extra = (table, filepath[:])
                # print "... New res: %r, %r, %r" % (res_be, res_fp, res_extra)
            if len(filepath) == 0:
                break
            query = filepath.pop(0)
            entry = table.get(query)
            if entry is not None:
                table = entry
                res_extra = (table, filepath[:])
            else:
                break
        if extra_info:
            return (res_be, res_fp) + res_extra
        else:
            return (res_be, res_fp)

    def resolve_to_backend(self, filepath):
        backend, filepath = self._resolve_to_backend(filepath)
        if backend is None:
            raise MountError("Path not mounted")
        return backend, filepath

    def __repr__(self, table=None, indent=[]):
        res = []
        if table is None:
            res.append("MountStorage<")
            table = self.mounttab
        v = table.get(None)
        if v:
            res.append("  " * len(indent) + repr(indent) + ": " + repr(v))
        for k, v in table.iteritems():
            if k == None:
                continue
            res.append("  " * len(indent) + repr(k) + ":")
            res += self.__repr__(v, indent + [k])
        if table is self.mounttab:
            res.append(">")
            return "\n".join(res)
        else:
            return res

    def file_exists(self, filepath):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.file_exists(filepath)

    def get_file(self, filepath, mode='r'):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.get_file(filepath, mode)

    def delete_file(self, filepath):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.delete_file(filepath)

    def file_url(self, filepath):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.file_url(filepath)

    def get_local_path(self, filepath):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.get_local_path(filepath)

    def copy_locally(self, filepath, dest_path):
        """
        Need to override copy_locally, because the local_storage
        attribute is not correct.
        """
        backend, filepath = self.resolve_to_backend(filepath)
        backend.copy_locally(filepath, dest_path)
