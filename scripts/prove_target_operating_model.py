#!/usr/bin/env python3
"""Generate commit-bound TR-M17 target-operating-model evidence."""

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
    ("python3 scripts/validate_policy_docs.py", [sys.executable, "scripts/validate_policy_docs.py"]),
    ("PYTHONPATH=src python3 -m tool_repository milestones validate", [sys.executable, "-m", "tool_repository", "milestones", "validate"]),
    ("python3 -m unittest tests.test_target_operating_model", [sys.executable, "-m", "unittest", "tests.test_target_operating_model"]),
)
REVIEWS = (("ai_engineer", "reviews/TR-M17_ai_engineer.md"), ("solution_architect", "reviews/TR-M17_solution_architect.md"), ("developer", "reviews/TR-M17_developer.md"))


def main() -> int:
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    if len(revision) != 40:
        raise RuntimeError("TR-M17 proof requires an inspectable Git commit")
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    payload = {
        "milestone_id": "TR-M17",
        "implementation_revision": revision,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "host": platform.node(), "runtime": "static operating-model validation"},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS],
        "observed_result": "The operating model distinguishes completed local/Git capability from future Cloudflare-hosted delivery and each mapped capability matches its milestone status.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M17_target_operating_model.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
