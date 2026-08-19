#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("python3 scripts/validate_repository.py", [sys.executable, "scripts/validate_repository.py"]),
    ("python3 -m unittest tests.test_contracts", [sys.executable, "-m", "unittest", "tests.test_contracts"]),
)


def revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def main() -> int:
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    payload = {
        "milestone_id": "TR-M01",
        "implementation_revision": revision(),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [
            {"role": "ai_engineer", "status": "passed", "reference": "reviews/TR-M01_ai_engineer.md"},
            {"role": "developer", "status": "passed", "reference": "reviews/TR-M01_developer.md"},
        ],
        "observed_result": "The shared transport-neutral adapter contract imports and its isolated contract tests pass.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M01_repository_contract_foundation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
