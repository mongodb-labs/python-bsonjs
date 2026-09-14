#!/usr/bin/env bash
set -eu

# Usage: bump-libbson.sh [LIBBSON_VERSION]
# With no argument, fetches the latest released mongo-c-driver tag. If the
# repo already pins that version, prints that it is up to date and exits
# without installing or benchmarking.

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SELF_DIR}/.." && pwd)"
BENCHMARK="${SELF_DIR}/benchmark.py"
BUMP_PY="${SELF_DIR}/bump_libbson.py"

# --- Determine the libbson version to bump to ---
CURRENT_VERSION=$(python3 "${BUMP_PY}" current)
LATEST_VERSION=$(python3 "${BUMP_PY}" latest)

if [ -z "${1:-}" ]; then
    LIBBSON_VERSION="$LATEST_VERSION"
    if [ "$LIBBSON_VERSION" == "$CURRENT_VERSION" ]; then
        echo "libbson is already up to date (${CURRENT_VERSION})."
        exit 0
    fi
    echo "Found latest libbson ${LATEST_VERSION}; current is ${CURRENT_VERSION}."
else
    LIBBSON_VERSION="$1"
fi

# 1. Update the libbson version in CMakeLists.txt, the README About line,
#    and the CHANGELOG 0.8.0 entry.
python3 "${BUMP_PY}" update-versions "$LIBBSON_VERSION"
echo "Updated libbson version to: ${LIBBSON_VERSION}"

# 2. Install the package and the latest stable pymongo.
cd "${REPO_ROOT}"
python3 -m pip install -e ".[test]"
python3 -m pip install --upgrade "pymongo>=4"

# 3. Run the benchmark, capturing raw output.
BENCHMARK_OUT=$(mktemp)
trap 'rm -f "$BENCHMARK_OUT"' EXIT
python3 "${BENCHMARK}" > "$BENCHMARK_OUT" 2>&1
echo "Benchmark:"
sed 's/^/  /' "$BENCHMARK_OUT"

# 4. Update the README Speed section with the results and versions.
PYMONGO_VERSION=$(python3 -c "import pymongo; print(pymongo.version)")
python3 "${BUMP_PY}" update-readme "$LIBBSON_VERSION" "$PYMONGO_VERSION" "$BENCHMARK_OUT"
echo "Updated README.rst (libbson ${LIBBSON_VERSION}, pymongo ${PYMONGO_VERSION})."
