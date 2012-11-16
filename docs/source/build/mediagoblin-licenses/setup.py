#!/usr/bin/env python
from distutils.core import setup
import re

from sys import version
assert version >= '2.6', 'This package requires python 2.6 at least. Sorry.'

def get_version():
    """Parse __init__.py for version info, we cannot import it"""
    version_re = re.compile(r'\s*__VERSION__\s*=\s*("|\')([\w\.\+]+)(\1)')
    with open('mediagoblin_licenses/__init__.py', 'rt') as file:
        for line in file:
            if version_re.match(line):
                return version_re.match(line).group(2)
__VERSION__ = get_version()


setup(name='mediagoblin-licenses',
      version=__VERSION__,
      description='Customize the licenses for your mediagoblin installation',
      author='Sebastian Spaeth',
      author_email='Sebastian@SSpaeth.de',
      url='https://gitorious.org/mediagoblin-licenses/mediagoblin-licenses',
      download_url='https://gitorious.org/mediagoblin-licenses/mediagoblin-licenses/archive-tarball/mediagoblin-licenses-v' + __VERSION__,
      # http://bugs.python.org/issue13943. Must not be unicode...
      packages=['mediagoblin_licenses'],
      package_data = {'mediagoblin_licenses': ['README.rst', 'COPYING']},
      license=(b'License :: OSI Approved :: GNU Affero General Public License '
               b'v3 or later (AGPLv3+)')
     )
