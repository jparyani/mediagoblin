#!/bin/sh

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

if [ -f ./bin/nosetests ]; then
    echo "Using ./bin/nosetests";
    export NOSETESTS="./bin/nosetests";
elif which nosetests > /dev/null; then
    echo "Using nosetests from \$PATH";
    export NOSETESTS="nosetests";
else
    echo "nosetests not found.  X_X";
    echo "Please install 'nose'.  Exiting.";
    exit 1
fi

need_arg=1
for i in "$@"
do
  case "$i" in
    -*) ;;
    *) need_arg=0; break ;;
  esac
done


CELERY_CONFIG_MODULE=mediagoblin.init.celery.from_tests
export CELERY_CONFIG_MODULE

if [ "$need_arg" = 1 ]
then
  dir="`dirname $0`"/mediagoblin/tests
  [ '!' -d "$dir" ] && dir=./mediagoblin/tests
  if [ '!' -d "$dir" ]
  then
    echo "Cound not find tests dir"
    exit 1
  fi
  $NOSETESTS "$@" "$dir"
else
  $NOSETESTS "$@"
fi
