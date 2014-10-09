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

from __future__ import print_function

from setuptools import setup, find_packages
from io import open
import os
import re

import sys

PY2 = sys.version_info[0] == 2  # six is not installed yet

READMEFILE = "README"
VERSIONFILE = os.path.join("mediagoblin", "_version.py")
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"


def get_version():
    with open(VERSIONFILE, "rt") as fobj:
        verstrline = fobj.read()
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." %
                           VERSIONFILE)

pyversion_install_requires = []
if PY2:
    pyversion_install_requires.append('argparse')  # only for < 2.7
    pyversion_install_requires.append('PasteScript')
    # newer sqlalchemy-migrate requires pbr which BREAKS EVERYTHING AND IS
    # TERRIBLE AND IS THE END OF ALL THINGS
    # I'd love to remove this restriction.
    pyversion_install_requires.append('sqlalchemy-migrate<0.8')
    # # Annoying.  Please remove once we can!  We only indirectly
    # # use pbr, and currently it breaks things, presumably till
    # # their next release.
    # pyversion_install_requires.append('pbr==0.5.22')
    pyversion_install_requires.append('mock')  # mock is in the stdlib for 3.3+
    # PyPI version (1.4.2) does not have proper Python 3 support
    pyversion_install_requires.append('ExifRead')
    pyversion_install_requires.append('PasteScript')
    pyversion_install_requires.append('Paste')
else:
    pyversion_install_requires.append('gunicorn')

install_requires = [
    'alembic==0.6.6',
    'python-dateutil',
    'wtforms',
    'py-bcrypt',
    'pytest>=2.3.1',
    'pytest-xdist',
    'werkzeug>=0.7',
    'celery>=3.0',
    'kombu',
    'jinja2',
    'Babel>=1.3',
    'webtest<2',
    'ConfigObj',
    'Markdown',
    'sqlalchemy<0.9.0, >0.8.0',
    'itsdangerous',
    'pytz',
    # PLEASE change this when we can; a dependency is forcing us to set this
    # specific number and it is breaking setup.py develop
    'six==1.5.2',
    'oauthlib',
    'unidecode',
    'jsonschema',
    'PasteDeploy',
    'requests',
    'pyld',
    # This is optional:
    # 'translitcodec',
    # For now we're expecting that users will install this from
    # their package managers.
    # 'lxml',
    # 'Pillow',
] + pyversion_install_requires

dependency_links = []
if not PY2:
    # PyPI version (1.4.2) does not have proper Python 3 support
    dependency_links.append('https://github.com/ianare/exif-py/zipball/develop#egg=ExifRead-2.0.0')
    install_requires.append('ExifRead>=2.0.0')

with open(READMEFILE, encoding="utf-8") as fobj:
    long_description = fobj.read()

try:
    setup(
    name="mediagoblin",
    version=get_version(),
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    zip_safe=False,
    include_package_data = True,
    # scripts and dependencies
    install_requires=install_requires,
    dependency_links=dependency_links,
    test_suite='nose.collector',
    entry_points="""\
        [console_scripts]
        gmg = mediagoblin.gmg_commands:main_cli
        pybabel = mediagoblin.babel.messages.frontend:main

        [paste.app_factory]
        app = mediagoblin.app:paste_app_factory

        [paste.server_runner]
        paste_server_selector = mediagoblin.app:paste_server_selector

        [paste.filter_app_factory]
        errors = mediagoblin.errormiddleware:mgoblin_error_middleware

        [zc.buildout]
        make_user_dev_dirs = mediagoblin.buildout_recipes:MakeUserDevDirs

        [babel.extractors]
        jinja2 = jinja2.ext:babel_extract
        """,
    license='AGPLv3',
    author='Free Software Foundation and contributors',
    author_email='cwebber@gnu.org',
    url="http://mediagoblin.org/",
    long_description=long_description,
    description='MediaGoblin is a web application for publishing all kinds of media',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content"
        ],
    )
except TypeError as e:
    import sys

    # Check if the problem is caused by the sqlalchemy/setuptools conflict
    msg_as_str = str(e)
    if not (msg_as_str == 'dist must be a Distribution instance'):
        raise

    # If so, tell the user it is OK to just run the script again.
    print("\n\n---------- NOTE ----------", file=sys.stderr)
    print("The setup.py command you ran failed.\n", file=sys.stderr)
    print("It is a known possible failure. Just run it again. It works the "
          "second time.", file=sys.stderr)
    sys.exit(1)
