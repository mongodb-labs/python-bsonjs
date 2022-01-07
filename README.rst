=============
python-bsonjs
=============

.. image:: https://travis-ci.org/mongodb-labs/python-bsonjs.svg?branch=master
   :alt: View build status
   :target: https://travis-ci.org/mongodb-labs/python-bsonjs

:Info: See `github <http://github.com/mongodb-labs/python-bsonjs>`_ for the latest source.
:Author: Shane Harvey <shane.harvey@mongodb.com>

About
=====

A fast BSON to MongoDB Extended JSON converter for Python that uses
`libbson  <http://mongoc.org/libbson/1.20.0/>`_.

Installation
============

python-bsonjs can be installed with `pip <http://pypi.python.org/pypi/pip>`_::

  $ python -m pip install python-bsonjs

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

Limitations
===========

Top Level Arrays
````````````````
Because `libbson` does not distinguish between top level arrays and top
level documents, neither does `python-bsonjs`. This means that if you give
`dumps` or `dump` a top level array it will give you back a dictionary.
Below are two examples of this behavior

.. code-block:: python

    >>> import bson
    >>> from bson import json_util
    >>> import bsonjs
    >>> bson.decode(bsonjs.loads(json_util.dumps(["a", "b", "c"])))
    {'0': 'a', '1': 'b', '2': 'c'}
    >>> bson.decode(bsonjs.loads(json_util.dumps([])))
    {}

One potential solution to this problem is to wrap your list in a dictionary,
like so

.. code-block:: python

    >>> list = ["a", "b", "c"]
    >>> dict = {"data": list}
    >>> wrapped = bson.decode(bsonjs.loads(json_util.dumps(dict)))
    {'data': ['a', 'b', 'c']}
    >>> wrapped["data"]
    ['a', 'b', 'c']

Installing From Source
======================

python-bsonjs supports CPython 3.6+.

Compiler
````````

You must build python-bsonjs separately for each version of Python. On
Windows this means you must use the same C compiler your Python version was
built with.

- Python 3.6 and up requires Microsoft Visual Studio 2015

Source
``````
You can download the source using git::

    $ git clone https://github.com/mongodb-labs/python-bsonjs.git


Install
```````

Once you have the source properly downloaded, build and install the package::

    $ python setup.py install

Test
````

To run the test suite::

    $ python setup.py test

