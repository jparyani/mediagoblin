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

import argparse
import os
import json
import logging
import subprocess
import pkg_resources

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import (
    FilenameBuilder, MediaProcessor,
    ProcessingManager, request_from_args,
    get_process_filename, store_public,
    copy_original)

from mediagoblin.media_types.stl import model_loader


_log = logging.getLogger(__name__)
SUPPORTED_FILETYPES = ['stl', 'obj']
MEDIA_TYPE = 'mediagoblin.media_types.stl'

BLEND_FILE = pkg_resources.resource_filename(
    'mediagoblin.media_types.stl',
    os.path.join(
        'assets',
        'blender_render.blend'))
BLEND_SCRIPT = pkg_resources.resource_filename(
    'mediagoblin.media_types.stl',
    os.path.join(
        'assets',
        'blender_render.py'))


def sniff_handler(media_file, filename):
    _log.info('Sniffing {0}'.format(MEDIA_TYPE))

    name, ext = os.path.splitext(filename)
    clean_ext = ext[1:].lower()

    if clean_ext in SUPPORTED_FILETYPES:
        _log.info('Found file extension in supported filetypes')
        return MEDIA_TYPE
    else:
        _log.debug('Media present, extension not found in {0}'.format(
                SUPPORTED_FILETYPES))

    return None


def blender_render(config):
    """
    Called to prerender a model.
    """
    env = {"RENDER_SETUP" : json.dumps(config), "DISPLAY":":0"}
    subprocess.call(
        ["blender",
         "-b", BLEND_FILE,
         "-F", "JPEG",
         "-P", BLEND_SCRIPT],
        env=env)


class CommonStlProcessor(MediaProcessor):
    """
    Provides a common base for various stl processing steps
    """
    acceptable_files = ['original']

    def common_setup(self):
        # Pull down and set up the processing file
        self.process_filename = get_process_filename(
            self.entry, self.workbench, self.acceptable_files)
        self.name_builder = FilenameBuilder(self.process_filename)

        self._set_ext()
        self._set_model()
        self._set_greatest()

    def _set_ext(self):
        ext = self.name_builder.ext[1:]

        if not ext:
            ext = None

        self.ext = ext

    def _set_model(self):
        """
        Attempt to parse the model file and divine some useful
        information about it.
        """
        with open(self.process_filename, 'rb') as model_file:
            self.model = model_loader.auto_detect(model_file, self.ext)

    def _set_greatest(self):
        greatest = [self.model.width, self.model.height, self.model.depth]
        greatest.sort()
        self.greatest = greatest[-1]

    def copy_original(self):
        copy_original(
            self.entry, self.process_filename,
            self.name_builder.fill('{basename}{ext}'))

    def _snap(self, keyname, name, camera, size, project="ORTHO"):
        filename = self.name_builder.fill(name)
        workbench_path = self.workbench.joinpath(filename)
        shot = {
            "model_path": self.process_filename,
            "model_ext": self.ext,
            "camera_coord": camera,
            "camera_focus": self.model.average,
            "camera_clip": self.greatest*10,
            "greatest": self.greatest,
            "projection": project,
            "width": size[0],
            "height": size[1],
            "out_file": workbench_path,
            }
        blender_render(shot)

        # make sure the image rendered to the workbench path
        assert os.path.exists(workbench_path)

        # copy it up!
        store_public(self.entry, keyname, workbench_path, filename)

    def _skip_processing(self, keyname, **kwargs):
        file_metadata = self.entry.get_file_metadata(keyname)

        if not file_metadata:
            return False
        skip = True

        if keyname == 'thumb':
            if kwargs.get('thumb_size') != file_metadata.get('thumb_size'):
                skip = False
        else:
            if kwargs.get('size') != file_metadata.get('size'):
                skip = False

        return skip

    def generate_thumb(self, thumb_size=None):
        if not thumb_size:
            thumb_size = (mgg.global_config['media:thumb']['max_width'],
                          mgg.global_config['media:thumb']['max_height'])

        if self._skip_processing('thumb', thumb_size=thumb_size):
            return

        self._snap(
            "thumb",
            "{basename}.thumb.jpg",
            [0, self.greatest*-1.5, self.greatest],
            thumb_size,
            project="PERSP")

        self.entry.set_file_metadata('thumb', thumb_size=thumb_size)

    def generate_perspective(self, size=None):
        if not size:
            size = (mgg.global_config['media:medium']['max_width'],
                    mgg.global_config['media:medium']['max_height'])

        if self._skip_processing('perspective', size=size):
            return

        self._snap(
            "perspective",
            "{basename}.perspective.jpg",
            [0, self.greatest*-1.5, self.greatest],
            size,
            project="PERSP")

        self.entry.set_file_metadata('perspective', size=size)

    def generate_topview(self, size=None):
        if not size:
            size = (mgg.global_config['media:medium']['max_width'],
                    mgg.global_config['media:medium']['max_height'])

        if self._skip_processing('top', size=size):
            return

        self._snap(
            "top",
            "{basename}.top.jpg",
            [self.model.average[0], self.model.average[1],
             self.greatest*2],
            size)

        self.entry.set_file_metadata('top', size=size)

    def generate_frontview(self, size=None):
        if not size:
            size = (mgg.global_config['media:medium']['max_width'],
                    mgg.global_config['media:medium']['max_height'])

        if self._skip_processing('front', size=size):
            return

        self._snap(
            "front",
            "{basename}.front.jpg",
            [self.model.average[0], self.greatest*-2,
             self.model.average[2]],
            size)

        self.entry.set_file_metadata('front', size=size)

    def generate_sideview(self, size=None):
        if not size:
            size = (mgg.global_config['media:medium']['max_width'],
                    mgg.global_config['media:medium']['max_height'])

        if self._skip_processing('side', size=size):
            return

        self._snap(
            "side",
            "{basename}.side.jpg",
            [self.greatest*-2, self.model.average[1],
             self.model.average[2]],
            size)

        self.entry.set_file_metadata('side', size=size)

    def store_dimensions(self):
        """
        Put model dimensions into the database
        """
        dimensions = {
            "center_x": self.model.average[0],
            "center_y": self.model.average[1],
            "center_z": self.model.average[2],
            "width": self.model.width,
            "height": self.model.height,
            "depth": self.model.depth,
            "file_type": self.ext,
            }
        self.entry.media_data_init(**dimensions)


class InitialProcessor(CommonStlProcessor):
    """
    Initial processing step for new stls
    """
    name = "initial"
    description = "Initial processing"

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
        """
        Determine if this media type is eligible for processing
        """
        if not state:
            state = entry.state
        return state in (
            "unprocessed", "failed")

    @classmethod
    def generate_parser(cls):
        parser = argparse.ArgumentParser(
            description=cls.description,
            prog=cls.name)

        parser.add_argument(
            '--size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        parser.add_argument(
            '--thumb_size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['size', 'thumb_size'])

    def process(self, size=None, thumb_size=None):
        self.common_setup()
        self.generate_thumb(thumb_size=thumb_size)
        self.generate_perspective(size=size)
        self.generate_topview(size=size)
        self.generate_frontview(size=size)
        self.generate_sideview(size=size)
        self.store_dimensions()
        self.copy_original()
        self.delete_queue_file()


class Resizer(CommonStlProcessor):
    """
    Resizing process steps for processed stls
    """
    name = 'resize'
    description = 'Resize thumbnail and mediums'
    thumb_size = 'size'

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
        """
        Determine if this media type is eligible for processing
        """
        if not state:
            state = entry.state
        return state in 'processed'

    @classmethod
    def generate_parser(cls):
        parser = argparse.ArgumentParser(
            description=cls.description,
            prog=cls.name)

        parser.add_argument(
            '--size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        parser.add_argument(
            'file',
            choices=['medium', 'thumb'])

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['size', 'file'])

    def process(self, file, size=None):
        self.common_setup()
        if file == 'medium':
            self.generate_perspective(size=size)
            self.generate_topview(size=size)
            self.generate_frontview(size=size)
            self.generate_sideview(size=size)
        elif file == 'thumb':
            self.generate_thumb(thumb_size=size)


class StlProcessingManager(ProcessingManager):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.add_processor(InitialProcessor)
        self.add_processor(Resizer)
