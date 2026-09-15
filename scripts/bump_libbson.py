#!/usr/bin/env python3
"""Version bump helper used by bump-libbson.sh."""

import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.rst"
CHANGELOG = REPO_ROOT / "CHANGELOG.rst"
MESON_BUILD = REPO_ROOT / "meson.build"

LATEST_RELEASE_URL = (
    "https://api.github.com/repos/mongodb/mongo-c-driver/releases/latest"
)
RELEASE_URL = (
    "https://github.com/mongodb/mongo-c-driver/releases/download/"
    "{version}/mongo-c-driver-{version}.tar.gz"
)


def package_version():
    """Return the package release version (X.Y.Z) from pyproject.toml."""
    text = (REPO_ROOT / "pyproject.toml").read_text()
    m = re.search(r'version\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit("Could not read the version from pyproject.toml")
    # Strip any dev/alpha/beta/rc suffix so we match the CHANGELOG header.
    return re.match(r"(\d+\.\d+(?:\.\d+)?)", m.group(1)).group(1)


def current_version():
    """Return the libbson version pinned in meson.build."""
    text = MESON_BUILD.read_text()
    m = re.search(r"mongo-c-driver-([0-9]+\.[0-9]+\.[0-9]+)", text)
    if not m:
        raise SystemExit("Could not read the libbson version from meson.build")
    return m.group(1)


def latest_version():
    """Return the latest released mongo-c-driver tag."""
    try:
        with urllib.request.urlopen(LATEST_RELEASE_URL, timeout=30) as resp:
            data = json.load(resp)
    except Exception as exc:
        raise SystemExit(
            "Could not fetch the latest mongo-c-driver release: {}".format(exc)
        )
    return data["tag_name"].lstrip("v")


def release_sha256(version):
    """Return the SHA256 of the mongo-c-driver release tarball."""
    url = RELEASE_URL.format(version=version)
    digest = hashlib.sha256()
    request = urllib.request.Request(url, headers={"User-Agent": "python-bsonjs"})
    try:
        with urllib.request.urlopen(request, timeout=180) as resp:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except Exception as exc:
        raise SystemExit("Could not download {}: {}".format(url, exc))
    return digest.hexdigest()


def sub_file(path, pattern, repl, label):
    """Replace the first match of pattern in path with repl.format(version)."""
    text = path.read_text()
    if not re.search(pattern, text):
        raise SystemExit("Could not update {} ({} not found)".format(path, label))
    path.write_text(re.sub(pattern, repl, text))


def update_versions(version):
    """Update the pinned libbson version in the build files and docs."""
    # Pin the libbson version in meson.build: the source-dir paths (fallback
    # and error message), the generated version header, and the three
    # libbson_major/minor/patch macros.
    major, minor, patch = version.split(".")
    text = MESON_BUILD.read_text()
    text = re.sub(
        r"mongo-c-driver-[0-9]+\.[0-9]+\.[0-9]+",
        "mongo-c-driver-{}".format(version),
        text,
    )
    text = re.sub(
        r"libbson_VERSION_FULL',\s*'[0-9]+\.[0-9]+\.[0-9]+'",
        "libbson_VERSION_FULL', '{}'".format(version),
        text,
    )
    text = re.sub(r"libbson_major = [0-9]+", "libbson_major = {}".format(major), text)
    text = re.sub(r"libbson_minor = [0-9]+", "libbson_minor = {}".format(minor), text)
    text = re.sub(r"libbson_patch = [0-9]+", "libbson_patch = {}".format(patch), text)
    if not re.search(r"mcd_sha256\s*=\s*'[0-9a-f]{64}'", text):
        raise SystemExit("Could not find mcd_sha256 in meson.build")
    text = re.sub(
        r"mcd_sha256\s*=\s*'[0-9a-f]{64}'",
        "mcd_sha256 = '{}'".format(release_sha256(version)),
        text,
    )
    MESON_BUILD.write_text(text)
    # README About link: http://mongoc.org/libbson/<ver>/
    sub_file(
        README,
        r"(mongoc\.org/libbson/)[0-9]+\.[0-9]+\.[0-9]+/",
        r"\g<1>{}/".format(version),
        "README About link",
    )
    # CHANGELOG section for the current package release. Scope the edits to
    # that section only so historic entries are left alone; the lower bound is
    # the next section header (any version), so future bumps stay correct.
    changelog = CHANGELOG.read_text()
    ver = re.escape(package_version())
    sec = re.search(
        r"(?ms)^{ver}\s*\n\s*```+\s*\n.*?(?=^\d+\.\d+\.\d+\s*\n\s*```+)".format(
            ver=ver
        ),
        changelog,
    )
    if not sec:
        raise SystemExit("Could not find the CHANGELOG {} section".format(ver))
    block = sec.group(0)
    patterns = (
        (r"libbson [0-9]+\.[0-9]+\.[0-9]+ from source",
         "libbson {} from source".format(version)),
        (r"mongo-c-driver/blob/[0-9]+\.[0-9]+\.[0-9]+/NEWS",
         "mongo-c-driver/blob/{}/NEWS".format(version)),
        (r"mongoc\.org/libbson/[0-9]+\.[0-9]+\.[0-9]+/",
         "mongoc.org/libbson/{}/".format(version)),
    )
    if not any(re.search(p, block) for p, _ in patterns):
        raise SystemExit("Could not update the CHANGELOG {} entry".format(ver))
    for pattern, repl in patterns:
        block = re.sub(pattern, repl, block)
    CHANGELOG.write_text(changelog[:sec.start()] + block + changelog[sec.end():])


def update_readme(version, pymongo_version, bench_path):
    """Rewrite the README Speed section using the measured benchmark output."""
    bench = Path(bench_path).read_text()

    ratios = [float(x) for x in re.findall(r"bsonjs is ([0-9.]+?)x faster", bench)]
    if len(ratios) != 2:
        raise SystemExit("Expected two benchmark ratios, got: {}".format(ratios))
    lo, hi = min(ratios), max(ratios)

    raw_numbers = re.findall(r"best of 3: ([0-9.e+-]+)", bench)
    if len(raw_numbers) != 4:
        raise SystemExit(
            "Expected four benchmark timings, got: {}".format(raw_numbers)
        )
    dumps_bsonjs, dumps_json_util, loads_bsonjs, loads_json_util = raw_numbers

    new_block = """Speed
=====

bsonjs is roughly {lo:.0f}-{hi:.0f}x faster than PyMongo {pymongo_version}'s
json_util at decoding BSON to JSON and encoding JSON to BSON. Benchmarked
against libbson {libbson_version}. See `scripts/benchmark.py`::

    $ python scripts/benchmark.py
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
        libbson_version=version,
        dumps_bsonjs=dumps_bsonjs,
        dumps_json_util=dumps_json_util,
        dumps_ratio=ratios[0],
        loads_bsonjs=loads_bsonjs,
        loads_json_util=loads_json_util,
        loads_ratio=ratios[1],
    )

    readme = README.read_text()
    speedy = re.compile(r"Speed\n=====\n\n.*?(?=\nLimitations)", re.DOTALL)
    if not speedy.search(readme):
        raise SystemExit("Could not find the Speed section in README.rst")
    README.write_text(speedy.sub(new_block, readme, count=1))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("current")
    sub.add_parser("latest")
    sub.add_parser("update-versions").add_argument("version")
    readme = sub.add_parser("update-readme")
    readme.add_argument("version")
    readme.add_argument("pymongo_version")
    readme.add_argument("bench_path")
    args = parser.parse_args()

    if args.cmd == "current":
        print(current_version())
    elif args.cmd == "latest":
        print(latest_version())
    elif args.cmd == "update-versions":
        update_versions(args.version)
    elif args.cmd == "update-readme":
        update_readme(args.version, args.pymongo_version, args.bench_path)


if __name__ == "__main__":
    main()
