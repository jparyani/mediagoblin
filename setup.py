from setuptools import setup, find_packages

import sys

setup(
    name = "mediagoblin",
    version = "0.0.1",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    zip_safe=False,
    # scripts and dependencies
    install_requires = [
        'setuptools',
        'PasteScript',
        'beaker',
        'routes',
        'pymongo',
        'mongokit',
        'webob',
        'wtforms',
        ],

    license = 'AGPLv3',
    author = 'Christopher Webber',
    author_email = 'cwebber@dustycloud.org',
    entry_points = """\
      [paste.app_factory]
      app = mediagoblin.app:paste_app_factory
      """,
    )
