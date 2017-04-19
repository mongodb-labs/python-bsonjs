#!/bin/bash

if [ "$#" -ne 0 ]; then
    echo "$0 takes no arguments"
    exit 1
fi

set -e -x

docker run --rm -v `pwd`:/io quay.io/pypa/manylinux1_x86_64 /io/build-wheels.sh /io
docker run --rm -v `pwd`:/io quay.io/pypa/manylinux1_i686 linux32 /io/build-wheels.sh /io
