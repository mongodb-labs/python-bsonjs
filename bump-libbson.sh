#!/usr/bin/env bash
set -eu

# Usage: bump-libbson.sh [LIBBSON_VERSION]
# Defaults to the latest released mongo-c-driver tag (libbson version).
LIBBSON_VERSION=${1:-"2.5.0"}

# 1. Update the libbson version in CMakeLists.txt (the FetchContent URL),
#    the README About line, and the CHANGELOG 0.8.0 entry.
python3 - "$LIBBSON_VERSION" <<'PY'
import re
import sys

version = sys.argv[1]


def sub_file(path, pattern, repl, label):
    with open(path) as f:
        text = f.read()
    if not re.search(pattern, text):
        raise SystemExit(
            "Could not update {} ({} not found)".format(path, label)
        )
    new = re.sub(pattern, repl.format(version), text)
    with open(path, "w") as f:
        f.write(new)


sub_file(
    "CMakeLists.txt",
    r"refs/tags/[0-9]+\.[0-9]+\.[0-9]+\.tar\.gz",
    "refs/tags/{}.tar.gz",
    "FetchContent URL",
)
# README About link: http://mongoc.org/libbson/<ver>/
sub_file(
    "README.rst",
    r"(mongoc\.org/libbson/)[0-9]+\.[0-9]+\.[0-9]+/",
    r"\g<1>{}/",
    "README About link",
)
# CHANGELOG 0.8.0 entry: the libbson mention and the two <ver> URLs. Scope
# the edits to the 0.8.0 section only so historic entries are left alone.
with open("CHANGELOG.rst") as f:
    changelog = f.read()

sec = re.search(r"(?ms)^0\.8\.0\s*\n\s*```+\s*\n.*?(?=\n0\.7\.0)", changelog)
if not sec:
    raise SystemExit("Could not find the CHANGELOG 0.8.0 section")
block = sec.group(0)
new_block = re.sub(
    r"libbson [0-9]+\.[0-9]+\.[0-9]+ from source",
    "libbson {} from source".format(version),
    block,
)
new_block = re.sub(
    r"mongo-c-driver/blob/[0-9]+\.[0-9]+\.[0-9]+/NEWS",
    "mongo-c-driver/blob/{}/NEWS".format(version),
    new_block,
)
new_block = re.sub(
    r"mongoc\.org/libbson/[0-9]+\.[0-9]+\.[0-9]+/",
    "mongoc.org/libbson/{}/".format(version),
    new_block,
)
if not any(
    re.search(p, block)
    for p in (
        r"libbson [0-9]+\.[0-9]+\.[0-9]+ from source",
        r"mongo-c-driver/blob/[0-9]+\.[0-9]+\.[0-9]+/NEWS",
        r"mongoc\.org/libbson/[0-9]+\.[0-9]+\.[0-9]+/",
    )
):
    raise SystemExit("Could not update the CHANGELOG 0.8.0 entry")
changelog = changelog[:sec.start()] + new_block + changelog[sec.end():]
with open("CHANGELOG.rst", "w") as f:
    f.write(changelog)
PY

echo "Updated libbson version to: ${LIBBSON_VERSION}"

# 2. Install the package and the latest stable pymongo.
python3 -m pip install -e ".[test]"
python3 -m pip install --upgrade "pymongo>=4"

# 3. Run the benchmark, capturing raw output.
BENCHMARK_OUT=$(mktemp)
python3 benchmark.py > "$BENCHMARK_OUT" 2>&1
echo "Benchmark:"
sed 's/^/  /' "$BENCHMARK_OUT"

# 4. Update the README Speed section with the results and versions.
PYMONGO_VERSION=$(python3 -c "import pymongo; print(pymongo.version)")
python3 - "$LIBBSON_VERSION" "$PYMONGO_VERSION" "$BENCHMARK_OUT" <<'PY'
import re
import sys

libbson_version, pymongo_version, bench_path = sys.argv[1], sys.argv[2], sys.argv[3]
readme_path = "README.rst"

with open(bench_path) as f:
    bench = f.read()

ratios = [
    float(x)
    for x in re.findall(r"bsonjs is ([0-9.]+?)x faster", bench)
]
if len(ratios) != 2:
    raise SystemExit("Expected two benchmark ratios, got: {}".format(ratios))

lo, hi = min(ratios), max(ratios)

raw_numbers = re.findall(r"best of 3: ([0-9.e+-]+)", bench)
if len(raw_numbers) != 4:
    raise SystemExit("Expected four benchmark timings, got: {}".format(raw_numbers))

dumps_bsonjs, dumps_json_util, loads_bsonjs, loads_json_util = raw_numbers

new_block = """Speed
=====

bsonjs is roughly {lo:.0f}-{hi:.0f}x faster than PyMongo {pymongo_version}'s
json_util at decoding BSON to JSON and encoding JSON to BSON. Benchmarked
against libbson {libbson_version}. See `benchmark.py`::

    $ python benchmark.py
    Timing: bsonjs.dumps(b)
    10000 loops, best of 3: {dumps_bsonjs}
    Timing: json_util.dumps(bson.decode(b))
    10000 loops, best of 3: {dumps_json_util}
    bsonjs is {dumps_ratio:.2f}x faster than json_util

    Timing: bsonjs.loads(j)
    10000 loops, best of 3: {loads_bsonjs}
    Timing: bson.encode(json_util.loads(j))
    10000 loops, best of 3: {loads_json_util}
    bsonjs is {loads_ratio:.2f}x faster than json_util
""".format(
    lo=lo,
    hi=hi,
    pymongo_version=pymongo_version,
    libbson_version=libbson_version,
    dumps_bsonjs=dumps_bsonjs,
    dumps_json_util=dumps_json_util,
    dumps_ratio=ratios[0],
    loads_bsonjs=loads_bsonjs,
    loads_json_util=loads_json_util,
    loads_ratio=ratios[1],
)

with open(readme_path) as f:
    readme = f.read()

speedy = re.compile(r"Speed\n=====\n\n.*?(?=\nLimitations)", re.DOTALL)
if not speedy.search(readme):
    raise SystemExit("Could not find the Speed section in README.rst")
readme = speedy.sub(new_block, readme, count=1)

with open(readme_path, "w") as f:
    f.write(readme)
PY

echo "Updated README.rst (libbson ${LIBBSON_VERSION}, pymongo ${PYMONGO_VERSION})."
