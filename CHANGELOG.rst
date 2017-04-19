Changelog
=========

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
