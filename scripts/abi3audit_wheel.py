#!/usr/bin/env python

# Copyright 2026 MongoDB, Inc.
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

"""Run abi3audit on a wheel, skipping wheels that are not abi3-tagged.

abi3audit only applies to abi3-tagged wheels: free-threaded wheels
(cp314t, cp315t, ...) are intentionally not abi3, since the limited API
is unsupported on free-threaded builds (PEP 703).

Run by the cibuildwheel repair step for every wheel, e.g.::

    python scripts/abi3audit_wheel.py <wheel>
"""

import shutil
import subprocess
import sys
from pathlib import Path


def is_abi3(wheel: Path) -> bool:
    """Check the wheel's abi tag (PEP 427: {dist}-{version}(-{build})?-{python}-{abi}-{platform})."""
    return wheel.name.removesuffix(".whl").split("-")[-2] == "abi3"


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <wheel>", file=sys.stderr)
        return 2

    wheel = Path(sys.argv[1])
    if not is_abi3(wheel):
        print(f"Skipping abi3audit for non-abi3 wheel: {wheel.name}")
        return 0

    if shutil.which("pipx") is not None:
        command = ["pipx", "run", "abi3audit"]
    elif shutil.which("uv") is not None:
        command = ["uv", "tool", "run", "abi3audit"]
    else:
        print("error: pipx or uv is required to run abi3audit", file=sys.stderr)
        return 1

    return subprocess.run(
        [*command, "--strict", "--report", str(wheel)],
        check=False,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
