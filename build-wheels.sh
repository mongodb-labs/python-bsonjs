#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "$0 requires one argument: <BSONJS_SOURCE_DIRECTORY>"
    echo "For example: $0 /user/home/git/python-bsonjs"
    exit 1
fi

set -e -x

BSONJS_SOURCE_DIRECTORY="$1"
cd "$BSONJS_SOURCE_DIRECTORY"

ls -la

# Compile wheels
/opt/python/cp36-cp36m/bin/python -m pip install wheel
# Build limited abi3 wheel.
/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
# https://github.com/pypa/manylinux/issues/49
rm -rf build

if [ "Linux" = "$(uname -s)" ]
then
  # Audit wheels and write multilinux1 tag
  for whl in dist/*.whl; do
      auditwheel repair "$whl" -w dist
  done
fi
ls -lah dist
