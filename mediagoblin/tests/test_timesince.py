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

from datetime import datetime, timedelta

from mediagoblin.tools.timesince import is_aware, timesince


def test_timesince(test_app):
	test_time = datetime.now()

	# it should ignore second and microseconds
	assert timesince(test_time, test_time + timedelta(microseconds=1)) == "0 minutes"
	assert timesince(test_time, test_time + timedelta(seconds=1)) == "0 minutes"

	# test minutes, hours, days, weeks, months and years (singular and plural)
	assert timesince(test_time, test_time + timedelta(minutes=1)) == "1 minute"
	assert timesince(test_time, test_time + timedelta(minutes=2)) == "2 minutes"

	assert timesince(test_time, test_time + timedelta(hours=1)) == "1 hour"
	assert timesince(test_time, test_time + timedelta(hours=2)) == "2 hours"

	assert timesince(test_time, test_time + timedelta(days=1)) == "1 day"
	assert timesince(test_time, test_time + timedelta(days=2)) == "2 days"

	assert timesince(test_time, test_time + timedelta(days=7)) == "1 week"
	assert timesince(test_time, test_time + timedelta(days=14)) == "2 weeks"

	assert timesince(test_time, test_time + timedelta(days=30)) == "1 month"
	assert timesince(test_time, test_time + timedelta(days=60)) == "2 months"

	assert timesince(test_time, test_time + timedelta(days=365)) == "1 year"
	assert timesince(test_time, test_time + timedelta(days=730)) == "2 years"

	# okay now we want to test combinations
	# 	e.g. 1 hour, 5 days
	assert timesince(test_time, test_time + timedelta(days=5, hours=1)) == "5 days, 1 hour"

	assert timesince(test_time, test_time + timedelta(days=15)) == "2 weeks, 1 day"

	assert timesince(test_time, test_time + timedelta(days=97)) == "3 months, 1 week"

	assert timesince(test_time, test_time + timedelta(days=2250)) == "6 years, 2 months"

