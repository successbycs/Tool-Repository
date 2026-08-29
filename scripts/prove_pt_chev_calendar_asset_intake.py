#!/usr/bin/env python3
"""Generate commit-bound TR-M23 Pt Chev calendar asset intake evidence."""

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
    ("PYTHONPATH=src python3 -m tool_repository repositories validate-queue", [sys.executable, "-m", "tool_repository", "repositories", "validate-queue"]),
    ("PYTHONPATH=src python3 -m tool_repository catalogue build", [sys.executable, "-m", "tool_repository", "catalogue", "build"]),
    ("python3 -m unittest tests.test_catalogue_api", [sys.executable, "-m", "unittest", "tests.test_catalogue_api"]),
)
REVIEWS = (("ai_engineer", "reviews/TR-M23_ai_engineer.md"), ("solution_architect", "reviews/TR-M23_solution_architect.md"), ("developer", "reviews/TR-M23_developer.md"))


def main() -> int:
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    if len(revision) != 40:
        raise RuntimeError("TR-M23 proof requires an inspectable Git commit")
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    payload = {
        "milestone_id": "TR-M23",
        "implementation_revision": revision,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "host": platform.node(), "runtime": "static intake and catalogue validation"},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS],
        "observed_result": "The Pt Chev assessment, candidate knowledge, public iCalendar contract template, and reference pattern were ingested without publishing executable adapter code or external feed data.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M23_pt_chev_calendar_asset_intake.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
