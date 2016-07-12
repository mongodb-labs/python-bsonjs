=============
python-bsonjs
=============
:Info: See `github <http://github.com/mongodb-labs/python-bsonjs>`_ for the latest source.
:Author: Shane Harvey <shane.harvey@mongodb.com>

About
=====

A fast BSON to MongoDB Extended JSON converter for Python.

Dependencies
============

python-bsonjs supports CPython 2.6, 2.7, and 3.3+.

Compiler
````````

You must build python-bsonjs separately for each version of Python. On
Windows this means you must use the same C compiler your Python version was
built with.

- Python 2.6 and 2.7 require `Microsoft Visual C++ Compiler for Python 2.7
  <https://www.microsoft.com/en-us/download/details.aspx?id=44266>`_
- Python 3.3 and 3.4 require Microsoft Visual Studio 2010 Professional
- Python 3.5 and up requires Microsoft Visual Studio 2015

Installing From Source
======================

Note that this repository contains a `git submodule
<https://git-scm.com/book/en/v2/Git-Tools-Submodules>`_. You must initialize
the submodule by using::

    $ git clone --recursive https://github.com/mongodb-labs/python-bsonjs.git

Or, if your version of git does not have ``clone --recursive``::

    $ git clone https://github.com/mongodb-labs/python-bsonjs.git
    $ cd python-bsonjs
    $ git submodule update --init --recursive

Once you have the source properly downloaded, install the package::

    $ python setup.py install

Tests
=====

To run the test suite::

    $ python setup.py test

Examples
========

.. code-block:: python

    >>> import bsonjs
    >>> bson_bytes = bsonjs.loads('{"hello": "world"}')
    >>> bson_bytes
    '\x16\x00\x00\x00\x02hello\x00\x06\x00\x00\x00world\x00\x00'
    >>> bsonjs.dumps(bson_bytes)
    '{ "hello" : "world" }'

Using bsonjs with pymongo to insert a RawBSONDocument.

.. code-block:: python

    >>> import bsonjs
    >>> from pymongo import MongoClient
    >>> from bson.raw_bson import RawBSONDocument
    >>> client = MongoClient("localhost", 27017, document_class=RawBSONDocument)
    >>> db = client.test
    >>> bson_bytes = bsonjs.loads('{"_id": 1, "x": 2}')
    >>> bson_bytes
    '\x15\x00\x00\x00\x10_id\x00\x01\x00\x00\x00\x10x\x00\x02\x00\x00\x00\x00'
    >>> result = db.test.insert_one(RawBSONDocument(bson_bytes))
    >>> result.inserted_id  # NOTE: inserted_id is None
    >>> result.acknowledged
    True
    >>> raw_doc = db.test.find_one({'x': 2})
    >>> raw_doc.raw == bson_bytes
    True
    >>> bsonjs.dumps(raw_doc.raw)
    '{ "_id" : 1, "x" : 2 }'

Speed
=====

bsonjs is roughly 10-15x faster than PyMongo's json_util at decoding BSON to
JSON and encoding JSON to BSON. See `benchmark.py`::
    $ python benchmark.py
    Timing: bsonjs.dumps(b)
    10000 loops, best of 3: 0.110911846161
    Timing: json_util.dumps(bson.BSON(b).decode())
    10000 loops, best of 3: 1.46571397781
    bsonjs is 13.22x faster than json_util

    Timing: bsonjs.loads(j)
    10000 loops, best of 3: 0.0628039836884
    Timing: bson.BSON().encode(json_util.loads(j))
    10000 loops, best of 3: 0.683200120926
    bsonjs is 11.72x faster than json_util
