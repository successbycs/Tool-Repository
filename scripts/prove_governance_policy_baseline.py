#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("python3 scripts/validate_policy_docs.py", [sys.executable, "scripts/validate_policy_docs.py"]),
    ("python3 -m unittest tests.test_policy_enforcement tests.test_milestone_governance", [sys.executable, "-m", "unittest", "tests.test_policy_enforcement", "tests.test_milestone_governance"]),
)


def revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def main() -> int:
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({
            "command": label,
            "exit_code": result.returncode,
            "output": output,
            "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        })
    payload = {
        "milestone_id": "TR-M00",
        "implementation_revision": revision(),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "observed_result": "Policy metadata and the milestone contract validate; the governance baseline tests pass.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M00_governance_policy_baseline.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
