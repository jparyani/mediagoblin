# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

setup(
    name = "mediagoblin",
    version = "0.0.2",
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
        'py-bcrypt',
        'nose',
        'werkzeug',
        'celery',
        'jinja2',
        'sphinx',
        'PIL',
        'Babel',
        'translitcodec',
        'argparse',
        ],
    test_suite='nose.collector',

    license = 'AGPLv3',
    author = 'Free Software Foundation and contributors',
    author_email = 'cwebber@gnu.org',
    entry_points = """\
      [console_scripts]
      gmg = mediagoblin.gmg_commands:main_cli

      [paste.app_factory]
      app = mediagoblin.app:paste_app_factory

      [zc.buildout]
      make_user_dev_dirs = mediagoblin.buildout_recipes:MakeUserDevDirs

      [babel.extractors]
      jinja2 = jinja2.ext:babel_extract
      """,
    )
