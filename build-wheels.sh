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
# Platform-dependent actions:
PYBIN=${PYTHON_BINARY:-"python"}
if [ "Linux" = "$(uname -s)" ]
then
  PYBIN=${PYTHON_BINARY:-"python3"}
fi
$PYBIN -m pip install wheel
$PYBIN setup.py bdist_wheel
# https://github.com/pypa/manylinux/issues/49
rm -rf build

if [ "Linux" = "$(uname -s)" ]
then
  # Audit wheels and write multilinux1 tag
  for whl in dist/*.whl; do
      auditwheel repair "$whl" -w dist
  done
  cp dist/*.whl ./wheelhouse
fi
ls -lah dist
