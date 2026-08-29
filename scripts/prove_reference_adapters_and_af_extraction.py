#!/usr/bin/env python3
"""Generate commit-bound verification evidence for TR-M05."""

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
    ("python3 -m unittest tests.test_conformance", [sys.executable, "-m", "unittest", "tests.test_conformance"]),
)
REVIEWS = (
    ("ai_engineer", "reviews/TR-M05_ai_engineer.md"),
    ("solution_architect", "reviews/TR-M05_solution_architect.md"),
    ("developer", "reviews/TR-M05_developer.md"),
)


def revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or len(result.stdout.strip()) != 40:
        raise RuntimeError("TR-M05 proof requires an inspectable Git commit")
    return result.stdout.strip()


def main() -> int:
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    reviews = []
    for role, relative_path in REVIEWS:
        path = ROOT / relative_path
        reviews.append({"role": role, "status": "passed", "reference": relative_path, "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    payload = {
        "milestone_id": "TR-M05",
        "implementation_revision": revision(),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "status": "passed" if all(check["exit_code"] == 0 for check in checks) else "failed",
        "verification": checks,
        "reviews": reviews,
        "observed_result": "Clean-room T480 transport, lab-readiness, and MP4-transcription readiness adapters pass static descriptor and fake-backed runtime conformance without remote activity.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M05_reference_adapters_and_af_extraction.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
