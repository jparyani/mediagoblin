#!/usr/bin/env python

from nose.tools import assert_equal, assert_true, assert_false

from mediagoblin import processing

class TestProcessing(object):
    def run_munge(self, input, format, output=None):
        munger = processing.FilenameMunger(input)
        result = munger.munge(format)
        if output is None:
            return result
        assert_equal(output, result)
        
    def test_easy_filename_munge(self):
        self.run_munge('/home/user/foo.TXT', '{basename}bar{ext}', 'foobar.txt')

    def test_long_filename_munge(self):
        self.run_munge('{0}.png'.format('A' * 300), 'image-{basename}{ext}',
                       'image-{0}.png'.format('A' * 245))
