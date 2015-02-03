#!/bin/bash
set -e

export HOME=/var
export TMPDIR=/var/tmp

rm -rf $TMPDIR
mkdir -p $TMPDIR
cp -r /etc/service /tmp
test -d /var/log || cp -r /var_original/log /var
test -d /var/lib || cp -r /var_original/lib /var
test -d /var/run || cp -r /var_original/run /var
test -e /var/lock || ln -s /var/run/lock /var/lock
test -f /var/mediagoblin.db || (cp /var_original/mediagoblin.db /var && echo "0.7.1" > /var/VERSION)
mkdir -p /var/user_dev

# Version migration
test -e /var/VERSION || echo "0.7.0" > /var/VERSION
[[ "$(cat /var/VERSION)" == "0.7.1" ]] || (cd /opt/app && echo "Upgrading Database...." && ./bin/gmg dbupdate && echo "0.7.1" > /var/VERSION)

cd /opt/app
./lazyserver.sh --server-name=broadcast 2>&1
