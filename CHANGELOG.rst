Changelog
=========

0.2.0
`````

Version 0.2.0 updates python-bsonjs's vendored copy of libbson to 1.6.5
http://mongoc.org/libbson/1.6.2/ and fixes an error in our Linux builds.

This update also adds support for the BSON decimal128 type encoded to json as
'{ "$numberDecimal" : "1.62" }'.

0.1.1
`````

Version 0.1.1 fixes a Windows build error.

First release 0.1.0
```````````````````

Version 0.1.0 is the first release of python-bsonjs!
This release uses libbson 1.3.5 http://mongoc.org/libbson/1.3.5/.