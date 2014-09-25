# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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

import collections
import tempfile
import shutil
import os
import pytest

from mediagoblin.media_types.pdf.processing import (
    pdf_info, check_prerequisites, create_pdf_thumb)
from .resources import GOOD_PDF


@pytest.mark.skipif("not os.path.exists(GOOD_PDF) or not check_prerequisites()")
def test_pdf():
    expected_dict = {'pdf_author': -1,
                     'pdf_creator': -1,
                     'pdf_keywords': -1,
                     'pdf_page_size_height': -1,
                     'pdf_page_size_width': -1,
                     'pdf_pages': -1,
                     'pdf_producer': -1,
                     'pdf_title': -1,
                     'pdf_version_major': 1,
                     'pdf_version_minor': -1}
    good_info = pdf_info(GOOD_PDF)
    for k, v in expected_dict.items():
        assert(k in good_info)
        assert(v == -1 or v == good_info[k])
    temp_dir = tempfile.mkdtemp()
    create_pdf_thumb(GOOD_PDF, os.path.join(temp_dir, 'good_256_256.png'), 256, 256)
    shutil.rmtree(temp_dir)
