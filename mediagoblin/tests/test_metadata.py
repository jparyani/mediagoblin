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

import pytest
from mediagoblin.tools.metadata import compact_and_validate
from jsonschema import ValidationError

class TestMetadataFunctionality:

    @pytest.fixture(autouse=True)
    def _setup(self, test_app):
        self.test_app = test_app

    def testCompactAndValidate(self):
        # First, test out a well formatted piece of metadata
        ######################################################
        test_metadata = {
            'dc:title':'My Pet Bunny',
            'dc:description':'A picture displaying how cute my pet bunny is.',
            'location':'/home/goblin/Pictures/bunny.png',
            'license':'http://www.gnu.org/licenses/gpl.txt'
        }
        jsonld_metadata =compact_and_validate(test_metadata)
        assert jsonld_metadata
        assert jsonld_metadata.get('dc:title') == 'My Pet Bunny'
        # Free floating nodes should be removed
        assert jsonld_metadata.get('location') is None
        assert jsonld_metadata.get('@context') == \
            u"http://www.w3.org/2013/json-ld-context/rdfa11"

        # Next, make sure that various badly formatted metadata
        # will be rejected.
        #######################################################
        #,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.
        # Metadata with a non-URI license should fail :
        #`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'
        metadata_fail_1 = {
            'dc:title':'My Pet Bunny',
            'dc:description':'A picture displaying how cute my pet bunny is.',
            'location':'/home/goblin/Pictures/bunny.png',
            'license':'All Rights Reserved.'
        }
        jsonld_fail_1 = None
        try:
            jsonld_fail_1 = compact_and_validate(metadata_fail_1)
        except ValidationError as e:
            assert e.message == "'All Rights Reserved.' is not a 'uri'"
        assert jsonld_fail_1 == None
        #,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,
        # Metadata with an ivalid date-time dc:created should fail :
        #`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`''
        metadata_fail_2 = {
            'dc:title':'My Pet Bunny',
            'dc:description':'A picture displaying how cute my pet bunny is.',
            'location':'/home/goblin/Pictures/bunny.png',
            'license':'http://www.gnu.org/licenses/gpl.txt',
            'dc:created':'The other day'
        }
        jsonld_fail_2 = None
        try:
            jsonld_fail_2 = compact_and_validate(metadata_fail_2)
        except ValidationError as e:
            assert e.message == "'The other day' is not a 'date-time'"
        assert jsonld_fail_2 == None

