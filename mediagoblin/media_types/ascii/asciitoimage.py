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

import Image
import ImageFont
import ImageDraw
import logging
import pkg_resources
import os

_log = logging.getLogger(__name__)


class AsciiToImage(object):
    '''
    Converter of ASCII art into image files, preserving whitespace

    kwargs:
    - font: Path to font file
      default: fonts/Inconsolata.otf
    - font_size: Font size, ``int``
      default: 11
    '''
    def __init__(self, **kw):
        self._font = kw.get('font', pkg_resources.resource_filename(
                'mediagoblin.media_types.ascii',
                os.path.join('fonts', 'Inconsolata.otf')))

        self._font_size = kw.get('font_size', 11)

        self._if = ImageFont.truetype(
            self._font,
            self._font_size,
            encoding='unic')

        _log.info('Font set to {0}, size {1}'.format(
                self._font,
                self._font_size))

        #      ,-,-^-'-^'^-^'^-'^-.
        #     ( I am a wall socket )Oo,  ___
        #      `-.,.-.,.-.-.,.-.--'     '   `
        # Get the size, in pixels of the '.' character
        self._if_dims = self._if.getsize('.')
        #                               `---'

    def convert(self, text, destination):
        # TODO: Detect if text is a file-like, if so, act accordingly
        im = self._create_image(text)

        # PIL's Image.save will handle both file-likes and paths
        if im.save(destination):
            _log.info('Saved image in {0}'.format(
                    destination))

    def _create_image(self, text):
        '''
        Write characters to a PIL image canvas.

        TODO:
        - Character set detection and decoding,
          http://pypi.python.org/pypi/chardet
        '''
        _log.debug('Drawing image')
        # Convert the input from str to unicode
        text = text.decode('utf-8')

        # TODO: Account for alternative line endings
        lines = text.split('\n')

        line_lengths = [len(i) for i in lines]

        # Calculate destination size based on text input and character size
        im_dims = (
            max(line_lengths) * self._if_dims[0],
            len(line_lengths) * self._if_dims[1])

        _log.info('Destination image dimensions will be {0}'.format(
                im_dims))

        im = Image.new(
            'RGBA',
            im_dims,
            (255, 255, 255, 0))

        draw = ImageDraw.Draw(im)

        char_pos = [0, 0]

        for line in lines:
            line_length = len(line)

            _log.debug('Writing line at {0}'.format(char_pos))

            for _pos in range(0, line_length):
                char = line[_pos]

                px_pos = self._px_pos(char_pos)

                _log.debug('Writing character "{0}" at {1} (px pos {2})'.format(
                        char.encode('ascii', 'replace'),
                        char_pos,
                        px_pos))

                draw.text(
                    px_pos,
                    char,
                    font=self._if,
                    fill=(0, 0, 0, 255))

                char_pos[0] += 1

            # Reset X position, increment Y position
            char_pos[0] = 0
            char_pos[1] += 1

        return im

    def _px_pos(self, char_pos):
        '''
        Helper function to calculate the pixel position based on
        character position and character dimensions
        '''
        px_pos = [0, 0]
        for index, val in zip(range(0, len(char_pos)), char_pos):
                px_pos[index] = char_pos[index] * self._if_dims[index]

        return px_pos
