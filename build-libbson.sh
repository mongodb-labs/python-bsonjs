#!/bin/bash -ex

set -o xtrace
set -o errexit

# Version of libbson to build.
LIBBSON_VERSION=${LIBBSON_VERSION:-"2.5.0"}
if [ -z "$LIBBSON_VERSION" ]
then
  echo "Did not provide a libbson revision ID to build"
  exit 1
fi

# Setup working directory
WORKDIR="mongo-c-driver-${LIBBSON_VERSION}"
if [ ! -d "$WORKDIR" ]
then
  git clone --depth 1 -b "$LIBBSON_VERSION" https://github.com/mongodb/mongo-c-driver.git "$WORKDIR"
fi

DEFAULT_ARCH=$(uname -m)
MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET:-"10.15"}
CMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES:-${DEFAULT_ARCH}}
CMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE:-"Release"}

DEFAULT_INSTALL_DIR=$(pwd)/libbson
LIBBSON_INSTALL_DIR=${LIBBSON_INSTALL_DIR:-${DEFAULT_INSTALL_DIR}}
LIBBSON_INSTALL_DIR="$(cd "$(dirname "$LIBBSON_INSTALL_DIR")"; pwd)/$(basename "$LIBBSON_INSTALL_DIR")"

echo "MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET}"
echo "CMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES}"
echo "LIBBSON_INSTALL_DIR=${LIBBSON_INSTALL_DIR}"

pushd "$WORKDIR"
  git checkout "$LIBBSON_VERSION"
  mkdir -p cmake-build
  pushd cmake-build
    cmake -DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF \
          -DENABLE_MONGOC=OFF \
          -DENABLE_SHARED=OFF \
          -DENABLE_STATIC=ON \
          -DBUILD_SHARED_LIBS=OFF \
          -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
          -DCMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES} \
          -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} \
          -DCMAKE_OSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET} \
          -DCMAKE_INSTALL_PREFIX:PATH="$LIBBSON_INSTALL_DIR" \
          ..
    cmake --build . --target clean
    cmake --build .
    cmake --build . --target install --config ${CMAKE_BUILD_TYPE}
  popd
popd
