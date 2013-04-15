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

import tempfile
import shutil
import os


from mediagoblin.media_types.pdf.processing import (
    pdf_info, check_prerequisites, create_pdf_thumb)

GOOD='mediagoblin/tests/test_submission/good.pdf'

def test_pdf():
    if not check_prerequisites():
        return
    good_dict = {'pdf_version_major': 1, 'pdf_title': '',
        'pdf_page_size_width': 612, 'pdf_author': '',
        'pdf_keywords': '', 'pdf_pages': 10,
        'pdf_producer': 'dvips + GNU Ghostscript 7.05',
        'pdf_version_minor': 3,
        'pdf_creator': 'LaTeX with hyperref package',
        'pdf_page_size_height': 792}
    assert pdf_info(GOOD) == good_dict
    temp_dir = tempfile.mkdtemp()
    create_pdf_thumb(GOOD, os.path.join(temp_dir, 'good_256_256.png'), 256, 256)
    shutil.rmtree(temp_dir)
