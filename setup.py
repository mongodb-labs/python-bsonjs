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
import re
import sys
from pathlib import Path

from setuptools import setup, Extension


def _read_version():
    """Read the package version from pyproject.toml.

    Keeps bsonjs.__version__ from drifting out of sync with the
    package version, since this extension has no pure-Python __init__.py
    to derive it from package metadata at import time instead.
    """
    text = (Path(__file__).parent / "pyproject.toml").read_text()
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError("Could not find version in pyproject.toml")
    return match.group(1)


libraries = []
if sys.platform == "win32":
    libraries.append("ws2_32")
elif sys.platform != "darwin":
    # librt may be needed for clock_gettime()
    libraries.append("rt")

setup(
    ext_modules=[
        Extension(
            "bsonjs",
            sources=["bsonjs/bsonjs.c"] + glob.glob("bsonjs/*/*.c"),
            include_dirs=["bsonjs",
                          "bsonjs/bson",
                          "bsonjs/jsonsl",
                          "bsonjs/common"],
            py_limited_api=True,
            define_macros=[("BSON_COMPILATION", 1),
                           ("Py_LIMITED_API", "0x03090000"),
                           ("BSONJS_VERSION", '"%s"' % _read_version())],
            libraries=libraries
        )
    ],
    options={'bdist_wheel': {'py_limited_api': 'cp39'} }
)
