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

import pkg_resources

from mediagoblin.init import config


CARROT_CONF_GOOD = pkg_resources.resource_filename(
    'mediagoblin.tests', 'fake_carrot_conf_good.ini')
CARROT_CONF_EMPTY = pkg_resources.resource_filename(
    'mediagoblin.tests', 'fake_carrot_conf_empty.ini')
CARROT_CONF_BAD = pkg_resources.resource_filename(
    'mediagoblin.tests', 'fake_carrot_conf_bad.ini')
FAKE_CONFIG_SPEC = pkg_resources.resource_filename(
    'mediagoblin.tests', 'fake_config_spec.ini')


def test_read_mediagoblin_config():
    # An empty file
    this_conf, validation_results = config.read_mediagoblin_config(
        CARROT_CONF_EMPTY, FAKE_CONFIG_SPEC)

    assert this_conf['carrotapp']['carrotcake'] == False
    assert this_conf['carrotapp']['num_carrots'] == 1
    assert 'encouragement_phrase' not in this_conf['carrotapp']
    assert this_conf['celery']['EAT_CELERY_WITH_CARROTS'] == True

    # A good file
    this_conf, validation_results = config.read_mediagoblin_config(
        CARROT_CONF_GOOD, FAKE_CONFIG_SPEC)

    assert this_conf['carrotapp']['carrotcake'] == True
    assert this_conf['carrotapp']['num_carrots'] == 88
    assert this_conf['carrotapp']['encouragement_phrase'] == \
        "I'd love it if you eat your carrots!"
    assert this_conf['carrotapp']['blah_blah'] == "blah!"
    assert this_conf['celery']['EAT_CELERY_WITH_CARROTS'] == False

    # A bad file
    this_conf, validation_results = config.read_mediagoblin_config(
        CARROT_CONF_BAD, FAKE_CONFIG_SPEC)

    # These should still open but will have errors that we'll test for
    # in test_generate_validation_report()
    assert this_conf['carrotapp']['carrotcake'] == 'slobber'
    assert this_conf['carrotapp']['num_carrots'] == 'GROSS'
    assert this_conf['carrotapp']['encouragement_phrase'] == \
        "586956856856"
    assert this_conf['carrotapp']['blah_blah'] == "blah!"
    assert this_conf['celery']['EAT_CELERY_WITH_CARROTS'] == "pants"


def test_generate_validation_report():
    # Empty
    this_conf, validation_results = config.read_mediagoblin_config(
        CARROT_CONF_EMPTY, FAKE_CONFIG_SPEC)
    report = config.generate_validation_report(this_conf, validation_results)
    assert report is None

    # Good
    this_conf, validation_results = config.read_mediagoblin_config(
        CARROT_CONF_GOOD, FAKE_CONFIG_SPEC)
    report = config.generate_validation_report(this_conf, validation_results)
    assert report is None

    # Bad
    this_conf, validation_results = config.read_mediagoblin_config(
        CARROT_CONF_BAD, FAKE_CONFIG_SPEC)
    report = config.generate_validation_report(this_conf, validation_results)

    assert report.startswith("""\
There were validation problems loading this config file:
--------------------------------------------------------""")

    expected_warnings = [
        'carrotapp:carrotcake = the value "slobber" is of the wrong type.',
        'carrotapp:num_carrots = the value "GROSS" is of the wrong type.',
        'celery:EAT_CELERY_WITH_CARROTS = the value "pants" is of the wrong type.']
    warnings = report.splitlines()[2:]

    assert len(warnings) == 3
    for warning in expected_warnings:
        assert warning in warnings
