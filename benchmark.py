#!/usr/bin/env python

# Copyright 2016 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Benchmark bsonjs vs bson.json_util"""

import sys
import timeit


def time(stmt, iterations, setup):
    print('Timing: ' + stmt)
    times = timeit.repeat(stmt=stmt, number=iterations, setup=setup)
    best = min(times)
    print('{0} loops, best of 3: {1}'.format(iterations, best))
    return best


def compare(bsonjs_stmt, json_util_stmt, iterations, setup):
    bsonjs_secs = time(bsonjs_stmt, iterations, setup)
    json_util_secs = time(json_util_stmt, iterations, setup)
    print('bsonjs is {0:.2f}x faster than json_util\n'.format(
        json_util_secs/bsonjs_secs))


def main(iterations):
    setup = ("import datetime\n"
             "import bsonjs\n"
             "import bson\n"
             "from bson import json_util\n"
             "doc = {\n"
             "    '_id': bson.ObjectId(),\n"
             "    'foo': [1, 2],\n"
             "    'bar': {'hello': 'world'},\n"
             "    'code': bson.Code('function x() { return 1; }'),\n"
             "    'bin': bson.Binary(b'\x01\x02\x03\x04'),\n"
             "    'min': bson.MinKey(),\n"
             "    'max': bson.MaxKey(),\n"
             "    'int64': bson.Int64(123),\n"
             "    'time': bson.Timestamp(4, 13),\n"
             "    'date': datetime.datetime(2009, 12, 9, 15),\n"
             "    'regex': bson.Regex('.*', 'i'),\n"
             "}\n"
             "b = bson.BSON.encode(doc)\n"
             "j = bsonjs.dumps(b)\n")

    # dumps
    compare("bsonjs.dumps(b)",
            "json_util.dumps(bson.BSON(b).decode())",
            iterations,
            setup)
    # loads
    compare("bsonjs.loads(j)",
            "bson.BSON().encode(json_util.loads(j))",
            iterations,
            setup)


def get_iterations():
    """Return number of iterations to perform"""
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            exit('usage: {0} [iterations]'.format(__file__))
    return 10000


if __name__ == "__main__":
    main(get_iterations())
