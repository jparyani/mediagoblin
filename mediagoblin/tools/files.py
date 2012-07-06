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

from mediagoblin import mg_globals

import os

def _jointhat(thing):
    if type(thing) == type(list()) or\
            type(thing) == type(tuple()):
        filepath = ""
        for item in thing:
            filepath = os.path.join(filepath, item)
        return filepath
    else:
        raise TypeError, "expecting a list or tuple, {0} received".format(
            str(type(thing)))

def delete_media_files(media):
    """
    Delete all files associated with a MediaEntry

    Arguments:
     - media: A MediaEntry document
    """
    no_such_files = []
    for listpath in media.media_files.itervalues():
        try:
            mg_globals.public_store.delete_file(
                listpath)
        except OSError:
            no_such_files.append(_jointhat(listpath))

    for attachment in media.attachment_files:
        try:
            mg_globals.public_store.delete_file(
                attachment['filepath'])
        except OSError:
            no_such_files.append(_jointhat(attachment))

    if no_such_files:
        # This breaks pep8 as far as I know
        raise OSError, ", ".join(no_such_files)
