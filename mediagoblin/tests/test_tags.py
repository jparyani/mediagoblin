# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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
from mediagoblin import util
from mediagoblin import mg_globals


@setup_fresh_app
def test_list_of_dicts_conversion(test_app):
    """
    When the user adds tags to a media entry, the string from the form is
    converted into a list of tags, where each tag is stored in the database
    as a dict. Each tag dict should contain the tag's name and slug. Another
    function performs the reverse operation when populating a form to edit tags.
    """
    # Leading, trailing, and internal whitespace should be removed and slugified
    assert util.convert_to_tag_list_of_dicts('sleep , 6    AM, chainsaw! ') == [
                              {'name': u'sleep', 'slug': u'sleep'},
                              {'name': u'6 AM', 'slug': u'6-am'},
                              {'name': u'chainsaw!', 'slug': u'chainsaw'}]

    # If the user enters two identical tags, record only one of them
    assert util.convert_to_tag_list_of_dicts('echo,echo') == [{'name': u'echo',
                                                               'slug': u'echo'}]

    # Make sure converting the list of dicts to a string works
    assert util.media_tags_as_string([{'name': u'yin', 'slug': u'yin'},
                                      {'name': u'yang', 'slug': u'yang'}]) == \
                                      u'yin,yang'

    # If the tag delimiter is a space then we expect different results
    mg_globals.app_config['tags_delimiter'] = u' '
    assert util.convert_to_tag_list_of_dicts('unicorn ceramic nazi') == [
                                       {'name': u'unicorn', 'slug': u'unicorn'},
                                       {'name': u'ceramic', 'slug': u'ceramic'},
                                       {'name': u'nazi', 'slug': u'nazi'}]
