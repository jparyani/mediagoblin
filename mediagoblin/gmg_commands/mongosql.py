# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2012 MediaGoblin contributors.  See AUTHORS.
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


def mongosql_parser_setup(subparser):
    pass


def mongosql(args):
    # First, make sure our mongo migrations are up to date...
    from mediagoblin.gmg_commands.migrate import run_migrate
    run_migrate(args.conf_file)

    from mediagoblin.db.sql.convert import run_conversion
    run_conversion(args.conf_file)
