#!/bin/bash -ex

if [ "$#" -ne 1 ]; then
    echo "$0 requires one argument: <BSONJS_SOURCE_DIRECTORY>"
    echo "For example: $0 /user/home/git/python-bsonjs"
    exit 1
fi

BSONJS_SOURCE_DIRECTORY="$1"
cd "$BSONJS_SOURCE_DIRECTORY"

ls -la
if [ -z "$PYTHON_BINARY" ]; then
  PYTHON_BINARY="python"
fi

$PYTHON_BINARY --version

if [ ! "$(uname)" == "Linux" ]; then
  $PYTHON_BINARY -m pip install wheel
fi
# Build limited abi3 wheel.
$PYTHON_BINARY setup.py bdist_wheel
# https://github.com/pypa/manylinux/issues/49
rm -rf build

# Audit wheels and write multilinux1 tag
# Only if on linux
if [ "$(uname)" == "Linux" ]; then
  for whl in dist/*.whl; do
      # Skip already built manylinux wheels.
      if [[ "$whl" != *"manylinux"* ]]; then
          auditwheel repair $whl -w dist
          rm $whl
      fi
  done
fi

# Install packages and test.
for PYBIN in /opt/python/*/bin; do
    if [[ ! "${PYBIN}" =~ (36|37|38|39|310) || "${PYBIN}" =~ (pypy) ]]; then
        continue
    fi
    "${PYBIN}/pip" install python-bsonjs --no-index -f dist
    # The tests require PyMongo.
    "${PYBIN}/pip" install 'pymongo>=3.4'
    for TEST_FILE in "${BSONJS_SOURCE_DIRECTORY}"/test/test_*.py; do
        "${PYBIN}/python" "$TEST_FILE" -v
    done
done

ls -lah dist
