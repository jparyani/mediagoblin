#!/bin/bash

# usage: maketarball [-d] <rev-ish>
#
# Creates a tarball from a rev-ish.  If -d is passed in, then it adds
# the date to the directory name.
#
# Examples:
#
#    ./maketarball -d master
#    ./maketarball v0.0.2

if [[ -z "$1" ]]; then
    echo "Usage: ./maketarball [-d] <rev-ish>";
    exit 1;
fi

NOWDATE=`date "+%Y-%m-%d"`

if [[ $@ == *-d* ]]; then
    REVISH=$2
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
