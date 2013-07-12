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
import logging
import dateutil.parser
from subprocess import PIPE, Popen

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import (create_pub_filepath,
                                    FilenameBuilder, BadMediaFail)
from mediagoblin.tools.translate import fake_ugettext_passthrough as _

_log = logging.getLogger(__name__)

MEDIA_TYPE = 'mediagoblin.media_types.pdf'

# TODO - cache (memoize) util

# This is a list created via uniconv --show and hand removing some types that
# we already support via other media types better.
unoconv_supported = [
  'bib', #      - BibTeX [.bib]
  #bmp      - Windows Bitmap [.bmp]
  'csv', #      - Text CSV [.csv]
  'dbf', #      - dBASE [.dbf]
  'dif', #      - Data Interchange Format [.dif]
  'doc6', #     - Microsoft Word 6.0 [.doc]
  'doc95', #    - Microsoft Word 95 [.doc]
  'docbook', #  - DocBook [.xml]
  'doc', #      - Microsoft Word 97/2000/XP [.doc]
  'docx7', #    - Microsoft Office Open XML [.docx]
  'docx', #     - Microsoft Office Open XML [.docx]
  #emf      - Enhanced Metafile [.emf]
  'eps', #      - Encapsulated PostScript [.eps]
  'fodp', #     - OpenDocument Presentation (Flat XML) [.fodp]
  'fods', #     - OpenDocument Spreadsheet (Flat XML) [.fods]
  'fodt', #     - OpenDocument Text (Flat XML) [.fodt]
  #gif      - Graphics Interchange Format [.gif]
  'html', #     - HTML Document (OpenOffice.org Writer) [.html]
  #jpg      - Joint Photographic Experts Group [.jpg]
  'latex', #    - LaTeX 2e [.ltx]
  'mediawiki', # - MediaWiki [.txt]
  'met', #      - OS/2 Metafile [.met]
  'odd', #      - OpenDocument Drawing [.odd]
  'odg', #      - ODF Drawing (Impress) [.odg]
  'odp', #      - ODF Presentation [.odp]
  'ods', #      - ODF Spreadsheet [.ods]
  'odt', #      - ODF Text Document [.odt]
  'ooxml', #    - Microsoft Office Open XML [.xml]
  'otg', #      - OpenDocument Drawing Template [.otg]
  'otp', #      - ODF Presentation Template [.otp]
  'ots', #      - ODF Spreadsheet Template [.ots]
  'ott', #      - Open Document Text [.ott]
  #pbm      - Portable Bitmap [.pbm]
  #pct      - Mac Pict [.pct]
  'pdb', #      - AportisDoc (Palm) [.pdb]
  #pdf      - Portable Document Format [.pdf]
  #pgm      - Portable Graymap [.pgm]
  #png      - Portable Network Graphic [.png]
  'pot', #      - Microsoft PowerPoint 97/2000/XP Template [.pot]
  'potm', #     - Microsoft PowerPoint 2007/2010 XML Template [.potm]
  #ppm      - Portable Pixelmap [.ppm]
  'pps', #      - Microsoft PowerPoint 97/2000/XP (Autoplay) [.pps]
  'ppt', #      - Microsoft PowerPoint 97/2000/XP [.ppt]
  'pptx', #     - Microsoft PowerPoint 2007/2010 XML [.pptx]
  'psw', #      - Pocket Word [.psw]
  'pwp', #      - PlaceWare [.pwp]
  'pxl', #      - Pocket Excel [.pxl]
  #ras      - Sun Raster Image [.ras]
  'rtf', #      - Rich Text Format [.rtf]
  'sda', #      - StarDraw 5.0 (OpenOffice.org Impress) [.sda]
  'sdc3', #     - StarCalc 3.0 [.sdc]
  'sdc4', #     - StarCalc 4.0 [.sdc]
  'sdc', #      - StarCalc 5.0 [.sdc]
  'sdd3', #     - StarDraw 3.0 (OpenOffice.org Impress) [.sdd]
  'sdd4', #     - StarImpress 4.0 [.sdd]
  'sdd', #      - StarImpress 5.0 [.sdd]
  'sdw3', #     - StarWriter 3.0 [.sdw]
  'sdw4', #     - StarWriter 4.0 [.sdw]
  'sdw', #      - StarWriter 5.0 [.sdw]
  'slk', #      - SYLK [.slk]
  'stc', #      - OpenOffice.org 1.0 Spreadsheet Template [.stc]
  'std', #      - OpenOffice.org 1.0 Drawing Template [.std]
  'sti', #      - OpenOffice.org 1.0 Presentation Template [.sti]
  'stw', #      - Open Office.org 1.0 Text Document Template [.stw]
  #svg      - Scalable Vector Graphics [.svg]
  'svm', #      - StarView Metafile [.svm]
  'swf', #      - Macromedia Flash (SWF) [.swf]
  'sxc', #      - OpenOffice.org 1.0 Spreadsheet [.sxc]
  'sxd3', #     - StarDraw 3.0 [.sxd]
  'sxd5', #     - StarDraw 5.0 [.sxd]
  'sxd', #      - OpenOffice.org 1.0 Drawing (OpenOffice.org Impress) [.sxd]
  'sxi', #      - OpenOffice.org 1.0 Presentation [.sxi]
  'sxw', #      - Open Office.org 1.0 Text Document [.sxw]
  #text     - Text Encoded [.txt]
  #tiff     - Tagged Image File Format [.tiff]
  #txt      - Text [.txt]
  'uop', #      - Unified Office Format presentation [.uop]
  'uos', #      - Unified Office Format spreadsheet [.uos]
  'uot', #      - Unified Office Format text [.uot]
  'vor3', #     - StarDraw 3.0 Template (OpenOffice.org Impress) [.vor]
  'vor4', #     - StarWriter 4.0 Template [.vor]
  'vor5', #     - StarDraw 5.0 Template (OpenOffice.org Impress) [.vor]
  'vor', #      - StarCalc 5.0 Template [.vor]
  #wmf      - Windows Metafile [.wmf]
  'xhtml', #    - XHTML Document [.html]
  'xls5', #     - Microsoft Excel 5.0 [.xls]
  'xls95', #    - Microsoft Excel 95 [.xls]
  'xls', #      - Microsoft Excel 97/2000/XP [.xls]
  'xlt5', #     - Microsoft Excel 5.0 Template [.xlt]
  'xlt95', #    - Microsoft Excel 95 Template [.xlt]
  'xlt', #      - Microsoft Excel 97/2000/XP Template [.xlt]
  #xpm      - X PixMap [.xpm]
]

def is_unoconv_working():
    # TODO: must have libreoffice-headless installed too, need to check for it
    unoconv = where('unoconv')
    if not unoconv:
        return False
    try:
        proc = Popen([unoconv, '--show'], stderr=PIPE)
        output = proc.stderr.read()
    except OSError, e:
        _log.warn(_('unoconv failing to run, check log file'))
        return False
    if 'ERROR' in output:
        return False
    return True

def supported_extensions(cache=[None]):
    if cache[0] == None:
        cache[0] = 'pdf'
        if is_unoconv_working():
            cache.extend(unoconv_supported)
    return cache

def where(name):
    for p in os.environ['PATH'].split(os.pathsep):
        fullpath = os.path.join(p, name)
        if os.path.exists(fullpath):
            return fullpath
    return None

def check_prerequisites():
    if not where('pdfinfo'):
        _log.warn('missing pdfinfo')
        return False
    if not where('pdftocairo'):
        _log.warn('missing pdfcairo')
        return False
    return True

def sniff_handler(media_file, **kw):
    _log.info('Sniffing {0}'.format(MEDIA_TYPE))
    if not check_prerequisites():
        return None
    if kw.get('media') is not None:
        name, ext = os.path.splitext(kw['media'].filename)
        clean_ext = ext[1:].lower()

        if clean_ext in supported_extensions():
            return MEDIA_TYPE

    return None

def create_pdf_thumb(original, thumb_filename, width, height):
    # Note: pdftocairo adds '.png', remove it
    thumb_filename = thumb_filename[:-4]
    executable = where('pdftocairo')
    args = [executable, '-scale-to', str(min(width, height)),
            '-singlefile', '-png', original, thumb_filename]
    _log.debug('calling {0}'.format(repr(' '.join(args))))
    Popen(executable=executable, args=args).wait()

def pdf_info(original):
    """
    Extract dictionary of pdf information. This could use a library instead
    of a process.

    Note: I'm assuming pdfinfo output is sanitized (integers where integers are
    expected, etc.) - if this is wrong then an exception will be raised and caught
    leading to the dreaded error page. It seems a safe assumption.
    """
    ret_dict = {}
    pdfinfo = where('pdfinfo')
    try:
        proc = Popen(executable=pdfinfo,
                     args=[pdfinfo, original], stdout=PIPE)
        lines = proc.stdout.readlines()
    except OSError:
        _log.debug('pdfinfo could not read the pdf file.')
        raise BadMediaFail()

    info_dict = dict([[part.strip() for part in l.strip().split(':', 1)]
                      for l in lines if ':' in l])

    for date_key in [('pdf_mod_date', 'ModDate'),
                     ('pdf_creation_date', 'CreationDate')]:
        if date_key in info_dict:
            ret_dict[date_key] = dateutil.parser.parse(info_dict[date_key])
    for db_key, int_key in [('pdf_pages', 'Pages')]:
        if int_key in info_dict:
            ret_dict[db_key] = int(info_dict[int_key])

    # parse 'PageSize' field: 595 x 842 pts (A4)
    page_size_parts = info_dict['Page size'].split()
    ret_dict['pdf_page_size_width'] = float(page_size_parts[0])
    ret_dict['pdf_page_size_height'] = float(page_size_parts[2])

    for db_key, str_key in [('pdf_keywords', 'Keywords'),
        ('pdf_creator', 'Creator'), ('pdf_producer', 'Producer'),
        ('pdf_author', 'Author'), ('pdf_title', 'Title')]:
        ret_dict[db_key] = info_dict.get(str_key, None)
    ret_dict['pdf_version_major'], ret_dict['pdf_version_minor'] = \
        map(int, info_dict['PDF version'].split('.'))

    return ret_dict

def process_pdf(proc_state):
    """Code to process a pdf file. Will be run by celery.

    A Workbench() represents a local tempory dir. It is automatically
    cleaned up when this function exits.
    """
    entry = proc_state.entry
    workbench = proc_state.workbench

    queued_filename = proc_state.get_queued_filename()
    name_builder = FilenameBuilder(queued_filename)

    # Copy our queued local workbench to its final destination
    original_dest = name_builder.fill('{basename}{ext}')
    proc_state.copy_original(original_dest)

    # Create a pdf if this is a different doc, store pdf for viewer
    ext = queued_filename.rsplit('.', 1)[-1].lower()
    if ext == 'pdf':
        pdf_filename = queued_filename
    else:
        pdf_filename = queued_filename.rsplit('.', 1)[0] + '.pdf'
        unoconv = where('unoconv')
        Popen(executable=unoconv,
              args=[unoconv, '-v', '-f', 'pdf', queued_filename]).wait()
        if not os.path.exists(pdf_filename):
            _log.debug('unoconv failed to convert file to pdf')
            raise BadMediaFail()
        proc_state.store_public(keyname=u'pdf', local_file=pdf_filename)

    pdf_info_dict = pdf_info(pdf_filename)

    for name, width, height in [
        (u'thumb', mgg.global_config['media:thumb']['max_width'],
                   mgg.global_config['media:thumb']['max_height']),
        (u'medium', mgg.global_config['media:medium']['max_width'],
                   mgg.global_config['media:medium']['max_height']),
        ]:
        filename = name_builder.fill('{basename}.%s.png' % name)
        path = workbench.joinpath(filename)
        create_pdf_thumb(pdf_filename, path, width, height)
        assert(os.path.exists(path))
        proc_state.store_public(keyname=name, local_file=path)

    proc_state.delete_queue_file()

    entry.media_data_init(**pdf_info_dict)
    entry.save()
