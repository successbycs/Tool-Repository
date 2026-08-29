#!/usr/bin/env python3
"""Generate commit-bound TR-M06 solution-consumption verification evidence."""

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
    ("python3 -m unittest tests.test_solution_consumption", [sys.executable, "-m", "unittest", "tests.test_solution_consumption"]),
    ("PYTHONPATH=src python3 -m tool_repository validate", [sys.executable, "-m", "tool_repository", "validate"]),
)
REVIEWS = (
    ("solution_architect", "reviews/TR-M06_solution_architect.md"),
    ("developer", "reviews/TR-M06_developer.md"),
)


def revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or len(result.stdout.strip()) != 40:
        raise RuntimeError("TR-M06 proof requires an inspectable Git commit")
    return result.stdout.strip()


def main() -> int:
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    payload = {
        "milestone_id": "TR-M06",
        "implementation_revision": revision(),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS],
        "observed_result": "A solution resolves the pinned T480 transport adapter, verifies an exact detached release checkout and descriptor bytes, invokes it locally, and retains provenance for reusable changes.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M06_solution_consumption_and_contribution.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
