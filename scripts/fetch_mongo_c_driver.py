#!/usr/bin/env python3
"""Fetch and extract the mongo-c-driver release pinned in meson.build."""

import argparse
import hashlib
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MESON_BUILD = REPO_ROOT / "meson.build"
DEFAULT_DEST = REPO_ROOT / ".mongo-c-driver"
RELEASE_URL = (
    "https://github.com/mongodb/mongo-c-driver/releases/download/"
    "{version}/mongo-c-driver-{version}.tar.gz"
)
CONFIG_H = "src/libbson/src/bson/config.h.in"


def _log(message):
    print(message, file=sys.stderr)


def _meson_value(pattern, description):
    match = re.search(pattern, MESON_BUILD.read_text(), re.MULTILINE)
    if not match:
        raise SystemExit("Could not read {} from meson.build".format(description))
    return match.group(1)


def pinned_version():
    """Return the mongo-c-driver version pinned in meson.build."""
    return _meson_value(
        r"mcd_version\s*=\s*'([0-9]+\.[0-9]+\.[0-9]+)'", "the mongo-c-driver version"
    )


def pinned_sha256():
    """Return the tarball SHA256 pinned in meson.build."""
    return _meson_value(r"mcd_sha256\s*=\s*'([0-9a-f]{64})'", "mcd_sha256")


def sha256_of(path):
    """Return the hex SHA256 digest of path."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, dest):
    """Download url to dest."""
    _log("[bsonjs] downloading {}".format(url))
    request = urllib.request.Request(url, headers={"User-Agent": "python-bsonjs"})
    with urllib.request.urlopen(request, timeout=180) as response, dest.open(
        "wb"
    ) as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)


def extract(tarball, dest_root):
    """Extract tarball into dest_root."""
    with tarfile.open(tarball) as archive:
        if sys.version_info >= (3, 12):
            archive.extractall(dest_root, filter="data")
        else:
            archive.extractall(dest_root)


def fetch(dest_root):
    """Ensure the pinned mongo-c-driver release is extracted under dest_root.

    Returns the extracted source directory. Reuses an existing extraction.
    """
    version = pinned_version()
    expected = pinned_sha256()
    srcdir = dest_root / "mongo-c-driver-{}".format(version)
    if (srcdir / CONFIG_H).is_file():
        _log("[bsonjs] mongo-c-driver {} already extracted".format(version))
        return srcdir
    dest_root.mkdir(parents=True, exist_ok=True)
    tarball = dest_root / "mongo-c-driver-{}.tar.gz".format(version)
    if tarball.is_file() and sha256_of(tarball) != expected:
        _log("[bsonjs] cached tarball checksum mismatch; re-downloading")
        tarball.unlink()
    if not tarball.is_file():
        download(RELEASE_URL.format(version=version), tarball)
    actual = sha256_of(tarball)
    if actual != expected:
        tarball.unlink()
        raise SystemExit(
            "SHA256 mismatch for mongo-c-driver {}: expected {}, got {}".format(
                version, expected, actual
            )
        )
    extract(tarball, dest_root)
    if not (srcdir / CONFIG_H).is_file():
        raise SystemExit("Extraction of mongo-c-driver {} failed".format(version))
    _log("[bsonjs] extracted mongo-c-driver {} to {}".format(version, srcdir))
    return srcdir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument(
        "--print-srcdir",
        action="store_true",
        help="print the extracted source directory to stdout",
    )
    args = parser.parse_args()
    srcdir = fetch(args.dest)
    if args.print_srcdir:
        print(srcdir)


if __name__ == "__main__":
    main()
