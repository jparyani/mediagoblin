#!/usr/bin/env python

from mediagoblin import processing

class TestProcessing(object):
    def run_fill(self, input, format, output=None):
        builder = processing.FilenameBuilder(input)
        result = builder.fill(format)
        if output is None:
            return result
        assert output == result
        
    def test_easy_filename_fill(self):
        self.run_fill('/home/user/foo.TXT', '{basename}bar{ext}', 'foobar.txt')

    def test_long_filename_fill(self):
        self.run_fill('{0}.png'.format('A' * 300), 'image-{basename}{ext}',
                      'image-{0}.png'.format('A' * 245))
