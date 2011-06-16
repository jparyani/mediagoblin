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
import pkg_resources

from configobj import ConfigObj
from validate import Validator


CONFIG_SPEC_PATH = pkg_resources.resource_filename(
    'mediagoblin', 'config_spec.ini')


def _setup_defaults(config, config_path):
    """
    Setup DEFAULTS in a config object from an (absolute) config_path.
    """
    config.setdefault('DEFAULT', {})
    config['DEFAULT']['here'] = os.path.dirname(config_path)
    config['DEFAULT']['__file__'] = config_path


def read_mediagoblin_config(config_path, config_spec=CONFIG_SPEC_PATH):
    """
    Read a config object from config_path.

    Does automatic value transformation based on the config_spec.
    Also provides %(__file__)s and %(here)s values of this file and
    its directory respectively similar to paste deploy.

    Args:
     - config_path: path to the config file
     - config_spec: config file that provides defaults and value types
       for validation / conversion.  Defaults to mediagoblin/config_spec.ini

    Returns:
      A read ConfigObj object.
    """
    config_path = os.path.abspath(config_path)

    config_spec = ConfigObj(
        CONFIG_SPEC_PATH,
        encoding='UTF8', list_values=False, _inspec=True)

    _setup_defaults(config_spec, config_path)

    conf = ConfigObj(
        config_path,
        configspec=config_spec,
        interpolation='ConfigParser')

    _setup_defaults(conf, config_path)

    conf.validate(Validator())

    return conf

