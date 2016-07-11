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

libbson
```````

To install libbson follow the installation `instructions for your system
<https://api.mongodb.com/libbson/current/installing.html>`_.

On Windows, you must add ``libbson\bin`` to your PATH environment variable.

pkg-config
``````````

pkg-config is used to find the appropriate options to build against libbson.

On RedHat/Fedora::

    $ sudo yum install pkg-config

On Debian/Ubuntu::

    $ sudo apt install pkg-config

On FreeBSD::

    $ su -c 'pkg install pkgconf'

On OS X::

    $ brew install pkg-config

On Windows:

pkg-config comes bundled with GTK+ for Windows. Download
`gtk+-bundle_2.22.0-20101016_win64.zip
<http://ftp.gnome.org/mirror/gnome.org/binaries/win64/gtk+/2.22/>`_,
extract, and add the ``gtk+-bundle_2.22.0-20101016_win64\bin`` folder to your
PATH environment variable.

Compiler
````````

You must build python-bsonjs separately for each version of Python. On
Windows this means you must use the same C compiler your Python version was
built with.

- Python 2.6 and 2.7 require `Microsoft Visual C++ Compiler for Python 2.7
<https://www.microsoft.com/en-us/download/details.aspx?id=44266>`_
- Python 3.3 and 3.4 require Microsoft Visual Studio 2010 Professional
- Python 3.5 and up requires Microsoft Visual Studio 2015

Bringing it all Together
````````````````````````

Download the source and install::

    $ git clone git@github.com:mongodb-labs/python-bsonjs.git
    $ cd python-bsonjs
    $ python setup.py install

Common Errors on Windows
````````````````````````

.. code-block:: python

    >>> import bsonjs
    Traceback (most recent call last):
      File "<stdin>", line 1 in <module>
    ImportError: DLL load failed: The specified module could not be found.

Add the libbson bin folder to your PATH environment variable.

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
