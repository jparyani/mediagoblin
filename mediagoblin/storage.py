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


from werkzeug.utils import secure_filename


def clean_listy_filepath(listy_filepath):
    """
    Take a listy filepath (like ['dir1', 'dir2', 'filename.jpg']) and
    clean out any nastiness from it.

    For example:
    >>> clean_listy_filepath([u'/dir1/', u'foo/../nasty', u'linooks.jpg'])
    [u'dir1', u'foo_.._nasty', u'linooks.jpg']

    Args:
    - listy_filepath: a list of filepath components, mediagoblin
      storage API style.

    Returns:
      A cleaned list of unicode objects.
    """
    return [
        unicode(secure_filename(filepath))
        for filepath in listy_filepath]


