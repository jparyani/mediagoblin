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

from setuptools import setup, find_packages
import os
import re

READMEFILE = "README"
VERSIONFILE = os.path.join("mediagoblin", "_version.py")
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"


def get_version():
    verstrline = open(VERSIONFILE, "rt").read()
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." %
                           VERSIONFILE)


setup(
    name="mediagoblin",
    version=get_version(),
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    zip_safe=False,
    include_package_data = True,
    # scripts and dependencies
    install_requires=[
        'setuptools',
        'PasteScript',
        'wtforms',
        'py-bcrypt',
        'pytest>=2.3.1',
        'pytest-xdist',
        'werkzeug>=0.7',
        'celery>=3.0',
        'kombu',
        'jinja2',
        'sphinx',
        'Babel<1.0',
        'argparse',
        'webtest<2',
        'ConfigObj',
        'Markdown',
        'sqlalchemy>=0.8.0',
        'sqlalchemy-migrate',
        'mock',
        'itsdangerous',
        'pytz',
        'six',
        'oauthlib==0.5.0',
        ## This is optional!
        # 'translitcodec',
        ## For now we're expecting that users will install this from
        ## their package managers.
        # 'lxml',
        # 'PIL',
        ],
    # requires=['gst'],
    test_suite='nose.collector',
    entry_points="""\
        [console_scripts]
        gmg = mediagoblin.gmg_commands:main_cli
        pybabel = mediagoblin.babel.messages.frontend:main

        [paste.app_factory]
        app = mediagoblin.app:paste_app_factory

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
    download_url="http://mediagoblin.org/download/",
    long_description=open(READMEFILE).read(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content"
        ],
    )
