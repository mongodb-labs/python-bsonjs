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

import glob
import sys


from setuptools import setup, Extension

with open("README.rst") as f:
    try:
        description = f.read()
    except Exception:
        description = ""

tests_require = ["pymongo>=3.4.0"]

libraries = []
if sys.platform == "win32":
    libraries.append("ws2_32")
elif sys.platform != "darwin":
    # librt may be needed for clock_gettime()
    libraries.append("rt")

setup(
    name="python-bsonjs",
    version="0.3.0",
    description="A library for converting between BSON and JSON.",
    long_description=description,
    author="Shane Harvey",
    author_email="shane.harvey@mongodb.com",
    url="https://github.com/mongodb-labs/python-bsonjs",
    keywords=["BSON", "JSON", "PyMongo"],
    test_suite="test",
    tests_require=tests_require,
    license="Apache License, Version 2.0",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython"],
    ext_modules=[
        Extension(
            "bsonjs",
            sources=["src/bsonjs.c"] + glob.glob("src/*/*.c"),
            include_dirs=["src",
                          "src/bson",
                          "src/jsonsl",
                          "src/common"],
            py_limited_api=True,
            define_macros=[("BSON_COMPILATION", 1),
                           ("Py_LIMITED_API", "0x03060000")],
            libraries=libraries
        )
    ]
)
