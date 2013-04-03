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

basedir="`dirname $0`"
# Directory to seaerch for:
subdir="mediagoblin/tests"
[ '!' -d "$basedir/$subdir" ] && basedir="."
if [ '!' -d "$basedir/$subdir" ]
then
  echo "Could not find base directory" >&2
  exit 1
fi

if [ -x "$basedir/bin/py.test" ]; then
    export PYTEST="$basedir/bin/py.test";
    echo "Using $PYTEST";
elif which py.test > /dev/null; then
    echo "Using py.test from \$PATH";
    export PYTEST="py.test";
else
    echo "py.test not found.  X_X";
    echo "Please install 'nose'.  Exiting.";
    exit 1
fi


CELERY_CONFIG_MODULE=mediagoblin.init.celery.from_tests
export CELERY_CONFIG_MODULE
echo "+ CELERY_CONFIG_MODULE=$CELERY_CONFIG_MODULE"

# Look to see if the user has specified a specific directory/file to
# run tests out of.  If not we'll need to pass along
# mediagoblin/tests/ later very specifically.  Otherwise py.test
# will try to read all directories, and this turns into a mess!

need_arg=1
for i in "$@"
do
  case "$i" in
    -*) ;;
    *) need_arg=0; break ;;
  esac
done

if [ "$need_arg" = 1 ]
then
  testdir="$basedir/mediagoblin/tests"
  set -x
  exec "$PYTEST" "$@" "$testdir" --boxed
else
  set -x
  exec "$PYTEST" "$@" --boxed
fi
