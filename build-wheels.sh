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
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/python" setup.py bdist_wheel
    # https://github.com/pypa/manylinux/issues/49
    rm -rf build
done

if [ "Linux" = "$(uname -s)" ]
  # Audit wheels and write multilinux1 tag
  for whl in dist/*.whl; do
      auditwheel repair "$whl" -w dist
  done
fi
# Install packages and test
if [ "Linux" = "$(uname -s)" ]
  for PYBIN in /opt/python/*/bin; do
      if [[ ! "${PYBIN}" =~ (36|37|38|39|310) ]]; then
          continue
      fi
      "${PYBIN}/pip" install python-bsonjs --no-index -f dist
      # The tests require PyMongo.
      "${PYBIN}/pip" install 'pymongo>=3.4' unittest2
      for TEST_FILE in "${BSONJS_SOURCE_DIRECTORY}"/test/test_*.py; do
          "${PYBIN}/python" "$TEST_FILE" -v
      done
  done
fi
ls -lah dist
