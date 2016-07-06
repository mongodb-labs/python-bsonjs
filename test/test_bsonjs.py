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

"""Test bsonjs against PyMongo's json_util."""

import datetime
import re
import sys
import uuid

sys.path.insert(0, "")

if sys.version_info[0] == 2:
    from StringIO import StringIO
else:
    from io import StringIO

if sys.version_info[:2] == (2, 6):
    import unittest2 as unittest
else:
    import unittest

import bson
from bson import json_util, EPOCH_AWARE
from bson.binary import Binary, MD5_SUBTYPE, USER_DEFINED_SUBTYPE
from bson.code import Code
from bson.codec_options import CodecOptions
from bson.dbref import DBRef
from bson.int64 import Int64
from bson.max_key import MaxKey
from bson.min_key import MinKey
from bson.objectid import ObjectId
from bson.regex import Regex
from bson.son import SON
from bson.timestamp import Timestamp
from bson.tz_util import utc

import bsonjs


def to_object(bson_bytes):
    """Return deserialized object from BSON bytes"""
    return bson.BSON(bson_bytes).decode(CodecOptions(document_class=SON,
                                                     tz_aware=True))


def to_bson(obj):
    """Return serialized BSON string from object"""
    return bson.BSON.encode(obj)


def bsonjs_dumps(doc):
    """Provide same API as json_util.dumps"""
    return bsonjs.dumps(to_bson(doc))


def bsonjs_loads(json_str):
    """Provide same API as json_util.loads"""
    return to_object(bsonjs.loads(json_str))


class TestBsonjs(unittest.TestCase):

    @staticmethod
    def round_tripped(doc):
        return bsonjs_loads(bsonjs_dumps(doc))

    def round_trip(self, doc):
        bson_bytes = to_bson(doc)
        self.assertEqual(doc, self.round_tripped(doc))
        # Check compatibility between bsonjs and json_util
        self.assertEqual(doc, json_util.loads(bsonjs.dumps(bson_bytes)))
        self.assertEqual(bson_bytes, bsonjs.loads(json_util.dumps(doc)))

    def test_basic(self):
        self.round_trip({"hello": "world"})

    def test_objectid(self):
        self.round_trip({"id": ObjectId()})

    def test_dbref(self):
        self.round_trip({"ref": DBRef("foo", 5)})
        self.round_trip({"ref": DBRef("foo", 5, "db")})
        self.round_trip({"ref": DBRef("foo", ObjectId())})

        # Order should be $ref then $id then $db
        self.assertEqual(
            '{ "ref" : { "$ref" : "collection", "$id" : 1, "$db" : "db" } }',
            bsonjs_dumps({"ref": DBRef("collection", 1, "db")}))

    @unittest.skip("CDRIVER-1339")
    def test_datetime(self):
        # only millis, not micros
        self.round_trip({"date": datetime.datetime(2009, 12, 9, 15,
                                                   49, 45, 191000, utc)})

        jsn = '{"dt": { "$date" : "1970-01-01T00:00:00.000+0000"}}'
        self.assertEqual(EPOCH_AWARE, bsonjs_loads(jsn)["dt"])
        jsn = '{"dt": { "$date" : "1970-01-01T00:00:00.000Z"}}'
        self.assertEqual(EPOCH_AWARE, bsonjs_loads(jsn)["dt"])
        # No explicit offset
        jsn = '{"dt": { "$date" : "1970-01-01T00:00:00.000"}}'
        self.assertEqual(EPOCH_AWARE, bsonjs_loads(jsn)["dt"])
        # Localtime behind UTC
        jsn = '{"dt": { "$date" : "1969-12-31T16:00:00.000-0800"}}'
        self.assertEqual(EPOCH_AWARE, bsonjs_loads(jsn)["dt"])
        # Localtime ahead of UTC
        jsn = '{"dt": { "$date" : "1970-01-01T01:00:00.000+0100"}}'
        self.assertEqual(EPOCH_AWARE, bsonjs_loads(jsn)["dt"])

        dtm = datetime.datetime(1, 1, 1, 1, 1, 1, 0, utc)
        jsn = '{"dt": {"$date": -62135593139000}}'
        self.assertEqual(dtm, bsonjs_loads(jsn)["dt"])
        jsn = '{"dt": {"$date": {"$numberLong": "-62135593139000"}}}'
        self.assertEqual(dtm, bsonjs_loads(jsn)["dt"])

    def test_regex(self):
        for regex_instance in (
                re.compile("a*b", re.IGNORECASE),
                Regex("a*b", re.IGNORECASE)):
            res = self.round_tripped({"r": regex_instance})["r"]

            self.assertEqual("a*b", res.pattern)
            res = self.round_tripped({"r": Regex("a*b", re.IGNORECASE)})["r"]
            self.assertEqual("a*b", res.pattern)
            self.assertEqual(re.IGNORECASE, res.flags)

        unicode_options = re.I | re.M | re.S | re.U | re.X
        regex = re.compile("a*b", unicode_options)
        res = self.round_tripped({"r": regex})["r"]
        self.assertEqual(unicode_options, res.flags)

        # Some tools may not add $options if no flags are set.
        res = bsonjs_loads('{"r": {"$regex": "a*b"}}')['r']
        self.assertEqual(0, res.flags)

        self.assertEqual(
            Regex(".*", "ilm"),
            bsonjs_loads(
                '{"r": {"$regex": ".*", "$options": "ilm"}}')['r'])

        # Order should be $regex then $options
        self.assertEqual(
            '{ "regex" : { "$regex" : ".*", "$options" : "mx" } }',
            bsonjs_dumps({"regex": Regex(".*", re.M | re.X)}))

        self.assertEqual(
            '{ "regex" : { "$regex" : ".*", "$options" : "mx" } }',
            bsonjs_dumps({"regex": re.compile(b".*", re.M | re.X)}))

    def test_minkey(self):
        self.round_trip({"m": MinKey()})

    def test_maxkey(self):
        self.round_trip({"m": MaxKey()})

    def test_timestamp(self):
        dct = {"ts": Timestamp(4, 13)}
        res = bsonjs_dumps(dct)
        self.assertEqual('{ "ts" : { "$timestamp" : { "t" : 4, "i" : 13 } } }',
                         res)

        rtdct = bsonjs_loads(res)
        self.assertEqual(dct, rtdct)

    @unittest.skip("PYTHON-1103")
    def test_uuid(self):
        self.round_trip({"uuid":
                         uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")})

    @unittest.skip("CDRIVER-1340,CDRIVER-1351")
    def test_binary(self):
        bin_type_dict = {"bin": Binary(b"\x00\x01\x02\x03\x04")}
        md5_type_dict = {
            "md5": Binary(b" n7\x18\xaf\t/\xd1\xd1/\x80\xca\xe7q\xcc\xac",
                          MD5_SUBTYPE)
        }
        custom_type_dict = {"custom": Binary(b"hello", USER_DEFINED_SUBTYPE)}

        self.round_trip(bin_type_dict)
        self.round_trip(md5_type_dict)
        self.round_trip(custom_type_dict)

        json_bin_dump = bsonjs_dumps(md5_type_dict)
        # Order should be $binary then $type.
        self.assertEqual(
            ('{ "md5" : { "$binary" : "IG43GK8JL9HRL4DK53HMrA==", '
             '"$type" : "05" } }'),
            json_bin_dump)

        json_bin_dump = bsonjs_dumps(custom_type_dict)
        self.assertTrue('"$type" : "80"' in json_bin_dump)
        # Check loading invalid binary
        self.assertRaises(ValueError, bsonjs.loads,
                          '{"a": {"$binary": "invalid", "$type": "80"}}')

    @unittest.skip("CDRIVER-1335")
    def test_code(self):
        self.round_trip({"code": Code("function x() { return 1; }")})
        code = {"code": Code("return z", z=2)}
        self.round_trip(code)

        # Check order.
        self.assertEqual('{"$code": "return z", "$scope": {"z": 2}}',
                         bsonjs_dumps(code))

    def test_undefined(self):
        json_str = '{"name": {"$undefined": true}}'
        self.round_trip(bsonjs_loads(json_str))
        self.assertIsNone(bsonjs_loads(json_str)['name'])

    def test_numberlong(self):
        json_str = '{"weight": {"$numberLong": "4611686018427387904"}}'
        self.round_trip(bsonjs_loads(json_str))
        self.assertEqual(bsonjs_loads(json_str)['weight'],
                         Int64(4611686018427387904))
        # Check loading invalid $numberLong
        self.assertRaises(ValueError, bsonjs.loads,
                          '{"a": {"$numberLong": 1}}')
        self.assertRaises(ValueError, bsonjs.loads,
                          '{"a": {"$numberLong": "not-a-number"}}')

    @unittest.skip("CDRIVER-1366")
    def test_load_mongodb_extended_type_at_top_level(self):
        self.assertRaises(ValueError, bsonjs.loads,
                          '{"$numberLong": "42"}')
        self.assertRaises(ValueError, bsonjs.loads,
                          '{"$numberLong": "42", "a": 1}')
        self.assertRaises(ValueError, bsonjs.loads,
                          '{"a": 1, "$numberLong": "42"}')

    def test_dumps_multiple_bson_documents(self):
        json_str = '{ "test" : "me" }'
        bson_bytes = bsonjs.loads(json_str)
        self.assertEqual(json_str, bsonjs.dumps(bson_bytes + bson_bytes))

    def test_loads_multiple_json_documents(self):
        json_str = '{ "test" : "me" }'
        self.assertEqual(bsonjs.loads(json_str), bsonjs.loads(json_str + "{}"))

    def test_dump_basic(self):
        json_str = '{ "test" : "me" }'
        bson_bytes = bsonjs.loads(json_str)
        filep = StringIO()
        bsonjs.dump(bson_bytes, filep)
        filep.seek(0)
        self.assertEqual(json_str, filep.read())

    def test_dump_throws_no_write_attribute(self):
        bson_bytes = bsonjs.loads('{ "test" : "me" }')
        not_file = {}
        self.assertRaises(AttributeError, bsonjs.dump, bson_bytes, not_file)

    def test_load_basic(self):
        json_str = '{ "test" : "me" }'
        filep = StringIO(json_str)
        self.assertEqual(bsonjs.loads(json_str), bsonjs.load(filep))

    def test_load_unicode(self):
        json_unicode = u'{ "test" : "me" }'

        class UnicodeRead(object):
            def read(self):
                return json_unicode
        self.assertEqual(bsonjs.loads(json_unicode),
                         bsonjs.load(UnicodeRead()))

    def test_load_throws_no_read_attribute(self):
        not_file = {}
        self.assertRaises(AttributeError, bsonjs.load, not_file)

if __name__ == "__main__":
    unittest.main()
