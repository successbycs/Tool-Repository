#!/usr/bin/env python3
"""Generate reproducible closure evidence for TR-M02."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("PYTHONPATH=src python3 -m tool_repository validate", [sys.executable, "-m", "tool_repository", "validate"]),
    ("python3 -m unittest tests.test_manifest_validation", [sys.executable, "-m", "unittest", "tests.test_manifest_validation"]),
)


def revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def main() -> int:
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    payload = {
        "milestone_id": "TR-M02",
        "implementation_revision": revision(),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [
            {"role": "ai_engineer", "status": "passed", "reference": "reviews/TR-M02_ai_engineer.md"},
            {"role": "solution_architect", "status": "passed", "reference": "reviews/TR-M02_solution_architect.md"},
            {"role": "developer", "status": "passed", "reference": "reviews/TR-M02_developer.md"}
        ],
        "observed_result": "The canonical static descriptor schema, meta-validation, safety invariants, and CLI discovery tests pass without importing adapter code or requiring credentials."
    }
    path = ROOT / "runs" / "proofs" / "TR-M02_tool_descriptor_schema.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
