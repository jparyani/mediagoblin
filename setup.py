from setuptools import setup, find_packages

import sys

setup(
    name = "mediagoblin",
    version = "0.0.1",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    zip_safe=False,
    license = 'AGPLv3',
    author = 'Christopher Webber',
    author_email = 'cwebber@dustycloud.org',
    entry_points = """\
      [paste.app_factory]
      mediagoblin = mediagoblin.app:paste_app_factory
      """,
    )
