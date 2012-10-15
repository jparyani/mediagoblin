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

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import create_pub_filepath, \
    FilenameBuilder

from mediagoblin.media_types.stl import model_loader


_log = logging.getLogger(__name__)
SUPPORTED_FILETYPES = ['stl', 'obj']


def sniff_handler(media_file, **kw):
    if kw.get('media') is not None:
        name, ext = os.path.splitext(kw['media'].filename)
        clean_ext = ext[1:].lower()
    
        if clean_ext in SUPPORTED_FILETYPES:
            _log.info('Found file extension in supported filetypes')
            return True
        else:
            _log.debug('Media present, extension not found in {0}'.format(
                    SUPPORTED_FILETYPES))
    else:
        _log.warning('Need additional information (keyword argument \'media\')'
                     ' to be able to handle sniffing')

    return False


def process_stl(entry):
    """
    Code to process an stl or obj model.
    """

    workbench = mgg.workbench_manager.create_workbench()
    # Conversions subdirectory to avoid collisions
    conversions_subdir = os.path.join(
        workbench.dir, 'conversions')
    os.mkdir(conversions_subdir)
    queued_filepath = entry.queued_media_file
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath, 'source')
    name_builder = FilenameBuilder(queued_filename)

    ext = queued_filename.lower().strip()[-4:]
    if ext.startswith("."):
        ext = ext[1:]
    else:
        ext = None

    # Attempt to parse the model file and divine some useful
    # information about it.
    with open(queued_filename, 'rb') as model_file:
        model = model_loader.auto_detect(model_file, ext)

    # TODO: generate blender previews

    # Save the public file stuffs
    model_filepath = create_pub_filepath(
        entry, name_builder.fill('{basename}{ext}'))

    with mgg.public_store.get_file(model_filepath, 'wb') as model_file:
        with open(queued_filename, 'rb') as queued_file:
            model_file.write(queued_file.read())


    # Remove queued media file from storage and database
    mgg.queue_store.delete_file(queued_filepath)
    entry.queued_media_file = []
        
    # Insert media file information into database
    media_files_dict = entry.setdefault('media_files', {})
    media_files_dict[u'original'] = model_filepath
    media_files_dict[u'thumb'] = ["mgoblin_static/images/404.png"]

    # Put model dimensions into the database
    dimensions = {
        "center_x" : model.average[0],
        "center_y" : model.average[1],
        "center_z" : model.average[2],
        "width" : model.width,
        "height" : model.height,
        "depth" : model.depth,
        }
    entry.media_data_init(**dimensions)

    # clean up workbench
    workbench.destroy_self()
