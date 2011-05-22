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


import os

from paste.deploy.loadwsgi import NicerConfigParser

from mediagoblin import app


def setup_app(args):
    """
    Setup the application after reading the mediagoblin config files
    """
    # Duplicated from from_celery.py, remove when we have the generic util
    parser = NicerConfigParser(args.conf_file)
    parser.read(args.conf_file)
    parser._defaults.setdefault(
        'here', os.path.dirname(os.path.abspath(args.conf_file)))
    parser._defaults.setdefault(
        '__file__', os.path.abspath(args.conf_file))

    mgoblin_section = dict(parser.items(args.app_section))
    mgoblin_conf = dict(
        [(section_name, dict(parser.items(section_name)))
         for section_name in parser.sections()])

    mgoblin_app = app.paste_app_factory(
        mgoblin_conf, **mgoblin_section)

    return mgoblin_app
