"""
Seed the full SMK3 audit dataset with 12 criteria and 166 clauses.

This script orchestrates the existing seed scripts in the required order:
1. create baseline criteria
2. replace clauses 1-105 with the detailed PLN Tenayan dataset
3. append clauses 106-166
"""

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).parent


def run_script(script_name: str) -> None:
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"{script_name} failed")


def main() -> None:
    run_script("populate_smk3_data.py")
    run_script("populate_all_166_clauses.py")
    run_script("add_remaining_61_clauses.py")
    print("SMK3 audit dataset seeded successfully with 12 criteria and 166 clauses.")


if __name__ == "__main__":
    main()
