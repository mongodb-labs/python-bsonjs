#!/bin/bash -ex

# Install cmake if the runner does not provide a compatible version.
if ! command -v cmake >/dev/null 2>&1; then
  pip install "cmake>=3.17,<4"
fi

# Set macOS architecture from cibuildwheel.
if [[ "$CIBW_BUILD" == *"macosx_"* ]]; then
  if [[ "$ARCHFLAGS" == *"arm64"* ]]; then
    export CMAKE_OSX_ARCHITECTURES="arm64"
  else
    export CMAKE_OSX_ARCHITECTURES="x86_64"
  fi
  export MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET:-"10.15"}
fi

CMAKE_BUILD_TYPE=Release bash ./build-libbson.sh
