#!/bin/bash

# usage: maketarball
#        maketarball <tag>
#
# With no arguments, this creates a source tarball from git master with a
# filename based on today's date.
#
# With a <tag> argument, this creates a tarball of the tag.
#
# Examples:
#
#    ./maketarball
#    ./maketarball v0.0.2

NOWDATE=`date "+%Y-%m-%d"`

if [ -z "$1" ]
then
    REVISH=master
    PREFIX="$NOWDATE-$REVISH"
else
    REVISH=$1
    PREFIX="$REVISH"
fi

# convert PREFIX to all lowercase.
# nix the v from tag names.
PREFIX=`echo "$PREFIX" | tr '[A-Z]' '[a-z]' | sed s/v//`

echo "== REVISH $REVISH"
echo "== PREFIX $PREFIX"

echo ""

echo "generating archive...."
git archive \
    --format=tar \
    --prefix=mediagoblin-$PREFIX/ \
    $REVISH > mediagoblin-$PREFIX.tar

if [[ $? -ne 0 ]]
then
    echo "git archive command failed.  See above text for reason."
    if [[ -e mediagoblin-$PREFIX.tar ]]
    then
        rm mediagoblin-$PREFIX.tar
    fi
    exit 1;
fi

echo "compressing...."
gzip mediagoblin-$PREFIX.tar

echo "archive at mediagoblin-$PREFIX.tar.gz"

echo "done."