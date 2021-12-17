#!/bin/bash -ex
cd ..
git clone git@github.com:mongodb/mongo-c-driver.git
cd mongo-c-driver
git clean -xdf
git checkout 1.20.0
python build/calc_release_version.py > VERSION_CURRENT
mkdir cmake-build && cd cmake-build
cmake -DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF -DENABLE_MONGOC=OFF ..
cd ../../
rm -r python-bsonjs/src/bson
rm -r python-bsonjs/src/jsonsl
rm -r python-bsonjs/src/common
rsync -r mongo-c-driver/src/libbson/src/bson/*.[hc] python-bsonjs/src/bson/
rsync -r mongo-c-driver/src/libbson/src/jsonsl/*.[hc] python-bsonjs/src/jsonsl/

rsync -r mongo-c-driver/src/common/*.[hc] python-bsonjs/src/common/
rsync -r mongo-c-driver/cmake-build/src/common/*.[hc] python-bsonjs/src/common/

rsync -r mongo-c-driver/cmake-build/src/libbson/src/bson/*.[hc] python-bsonjs/src/bson/
rsync -r mongo-c-driver/cmake-build/src/libbson/src/jsonsl/*.[hc] python-bsonjs/src/jsonsl/