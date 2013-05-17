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

from mediagoblin.tools import text

def test_list_of_dicts_conversion(test_app):
    """
    When the user adds tags to a media entry, the string from the form is
    converted into a list of tags, where each tag is stored in the database
    as a dict. Each tag dict should contain the tag's name and slug. Another
    function performs the reverse operation when populating a form to edit tags.
    """
    # Leading, trailing, and internal whitespace should be removed and slugified
    assert text.convert_to_tag_list_of_dicts('sleep , 6    AM, chainsaw! ') == [
                              {'name': u'sleep', 'slug': u'sleep'},
                              {'name': u'6 AM', 'slug': u'6-am'},
                              {'name': u'chainsaw!', 'slug': u'chainsaw'}]

    # If the user enters two identical tags, record only one of them
    assert text.convert_to_tag_list_of_dicts('echo,echo') == [{'name': u'echo',
                                                               'slug': u'echo'}]

    # Make sure converting the list of dicts to a string works
    assert text.media_tags_as_string([{'name': u'yin', 'slug': u'yin'},
                                      {'name': u'yang', 'slug': u'yang'}]) == \
                                      u'yin, yang'
