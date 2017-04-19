#!/bin/bash

if [ "$#" -ne 0 ]; then
    echo "$0 takes no arguments"
    exit 1
fi

set -e -x


DOCKER_IMAGE=quay.io/pypa/manylinux1_x86_64
docker pull "$DOCKER_IMAGE"
docker run --rm -v `pwd`:/io "$DOCKER_IMAGE" /io/build-wheels.sh /io

DOCKER_IMAGE=quay.io/pypa/manylinux1_i686
docker pull "$DOCKER_IMAGE"
docker run --rm -v `pwd`:/io "$DOCKER_IMAGE" linux32 /io/build-wheels.sh /io
