Changelog
=========

0.5.0
`````
Version 0.5.0 updates python-bsonjs's vendored copy of libbson to 1.27.6.
For a detailed breakdown of what changed in each version of libbson see its changelog:
https://github.com/mongodb/mongo-c-driver/blob/1.27.6/src/libbson/NEWS
http://mongoc.org/libbson/1.27.6/

This release also adds support for Python 3.13 and drops support for Python 3.7.

0.4.0
`````
Version 0.4.0 updates python-bsonjs's vendored copy of libbson to 1.24.2.
For a detailed breakdown of what changed in each version of libbson see its changelog:
https://github.com/mongodb/mongo-c-driver/blob/1.24.2/src/libbson/NEWS
http://mongoc.org/libbson/1.24.2/

This release also adds support for Python 3.11 and 3.12.

0.3.0
`````

Version 0.3.0 updates python-bsonjs's vendored copy of libbson to 1.20.0.
For a detailed breakdown of what changed in each version of libbson see its changelog:
https://github.com/mongodb/mongo-c-driver/blob/1.20.0/src/libbson/NEWS
http://mongoc.org/libbson/1.20.0/

This release also provides a number of improvements and features:

- Added support for Python 3.7, 3.8, 3.9, and 3.10
- Added a new keyword argument to the `dumps` and `dump` functions: `mode`. It
  can be one of: bsonjs.LEGACY, bsonjs.CANONICAL, or bsonjs.RELAXED. Which are:
  libbson's legacy extended JSON format, MongoDB Extended JSON 2.0 canonical
  mode, and MongoDB Extended JSON relaxed mode.
- Dropped support for Python 2.7, 3.4, and 3.5.


0.2.0
`````

Version 0.2.0 updates python-bsonjs's vendored copy of libbson to 1.6.5
http://mongoc.org/libbson/1.6.2/.
Updating libbson provides a number of improvements and features including:

- Use jsonsl instead of libyajl as our JSON parsing library, parse JSON more
  strictly, fix minor parsing bugs.
- Extended JSON documents like '{"$code": "...", "$scope": {}}' are now parsed
  into BSON "code" elements.
- ISO8601 dates now allow years from 0000 to 9999 inclusive. Before, years
  before 1970 were prohibited.
- BSON floats and ints are now distinguished in JSON output.
- Support for the BSON decimal128 type encoded to json as
  '{ "$numberDecimal" : "1.62" }'.

This release also fixes an error in our Linux builds. Previously published
releases for Python 3.3 and 3.4 on Linux are broken due to the following
error::

    >>> import bsonjs
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    ImportError: /path/to/bsonjs.cpython-34m.so: undefined symbol: clock_gettime

0.1.1
`````

Version 0.1.1 fixes a Windows build error.

0.1.0
`````

Version 0.1.0 is the first release of python-bsonjs!
This release uses libbson 1.3.5 http://mongoc.org/libbson/1.3.5/.
