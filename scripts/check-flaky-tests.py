from __future__ import annotations

import subprocess
import sys

RUNS = 3
COMMAND = ["uv", "run", "pytest", "tests/unit", "-q", "--cov-fail-under=0"]


def main() -> int:
    for run_number in range(1, RUNS + 1):
        print(f"Flaky check run {run_number}/{RUNS}: {' '.join(COMMAND)}")
        completed = subprocess.run(COMMAND, check=False)
        if completed.returncode != 0:
            print(f"Unit test run {run_number} failed, indicating a flaky or broken fast path.")
            return completed.returncode
    print("Flaky check passed across repeated unit-test runs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
