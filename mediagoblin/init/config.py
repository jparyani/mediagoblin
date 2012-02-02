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

import os
import pkg_resources

from configobj import ConfigObj, flatten_errors
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

    This function doesn't itself raise any exceptions if validation
    fails, you'll have to do something

    Args:
     - config_path: path to the config file
     - config_spec: config file that provides defaults and value types
       for validation / conversion.  Defaults to mediagoblin/config_spec.ini

    Returns:
      A tuple like: (config, validation_result)
      ... where 'conf' is the parsed config object and 'validation_result'
      is the information from the validation process.
    """
    config_path = os.path.abspath(config_path)

    config_spec = ConfigObj(
        config_spec,
        encoding='UTF8', list_values=False, _inspec=True)

    _setup_defaults(config_spec, config_path)

    config = ConfigObj(
        config_path,
        configspec=config_spec,
        interpolation='ConfigParser')

    _setup_defaults(config, config_path)

    # For now the validator just works with the default functions,
    # but in the future if we want to add additional validation/configuration
    # functions we'd add them to validator.functions here.
    #
    # See also:
    #   http://www.voidspace.org.uk/python/validate.html#adding-functions
    validator = Validator()
    validation_result = config.validate(validator, preserve_errors=True)

    return config, validation_result


REPORT_HEADER = u"""\
There were validation problems loading this config file:
--------------------------------------------------------
"""


def generate_validation_report(config, validation_result):
    """
    Generate a report if necessary of problems while validating.

    Returns:
      Either a string describing for a user the problems validating
      this config or None if there are no problems.
    """
    report = []

    # Organize the report
    for entry in flatten_errors(config, validation_result):
        # each entry is a tuple
        section_list, key, error = entry

        if key is not None:
            section_list.append(key)
        else:
            section_list.append(u'[missing section]')

        section_string = u':'.join(section_list)

        if error == False:
            # We don't care about missing values for now.
            continue

        report.append(u"%s = %s" % (section_string, error))

    if report:
        return REPORT_HEADER + u"\n".join(report)
    else:
        return None
