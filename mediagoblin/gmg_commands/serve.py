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

from paste.deploy import loadapp, loadserver


class ServeCommand(object):

    def loadserver(self, server_spec, name, relative_to, **kwargs):
        return loadserver(server_spec, name=name, relative_to=relative_to,
                          **kwargs)

    def loadapp(self, app_spec, name, relative_to, **kwargs):
        return loadapp(app_spec, name=name, relative_to=relative_to, **kwargs)

    def daemonize(self):
        # TODO: pass to gunicorn if available
        pass

    def restart_with_reloader(self):
        pass

    def restart_with_monitor(self, reloader=False):
        pass

    def run(self):
        print('Running...')


def parser_setup(subparser):
    subparser.add_argument('config', metavar='CONFIG_FILE')
    subparser.add_argument('command',
                           choices=['start', 'stop', 'restart', 'status'],
                           nargs='?', default='start')
    subparser.add_argument('-n', '--app-name',
                           dest='app_name',
                           metavar='NAME',
                           help="Load the named application (default main)")
    subparser.add_argument('-s', '--server',
                           dest='server',
                           metavar='SERVER_TYPE',
                           help="Use the named server.")
    subparser.add_argument('--reload',
                           dest='reload',
                           action='store_true',
                           help="Use auto-restart file monitor")


def serve(args):
    serve_cmd = ServeCommand()  # TODO: pass args to it
    serve_cmd.run()
