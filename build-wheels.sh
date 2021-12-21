#!/bin/bash -ex

if [ "$#" -ne 1 ]; then
    echo "$0 requires one argument: <BSONJS_SOURCE_DIRECTORY>"
    echo "For example: $0 /user/home/git/python-bsonjs"
    exit 1
fi

BSONJS_SOURCE_DIRECTORY="$1"
cd "$BSONJS_SOURCE_DIRECTORY"

ls -la

# Build limited abi3 wheel.
/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
# https://github.com/pypa/manylinux/issues/49
rm -rf build

# Audit wheels and write manylinux tag.
for whl in dist/*.whl; do
    # Skip already built manylinux wheels.
    if [[ "$whl" != *"manylinux"* ]]; then
        auditwheel repair $whl -w dist
        rm $whl
    fi
done

# Install packages and test.
for PYBIN in /opt/python/*/bin; do
    if [[ ! "${PYBIN}" =~ (36|37|38|39|310) ]]; then
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
