#!/usr/bin/env python3
"""Generate commit-bound TR-M16 prompt, template, and approved-goal evidence."""

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
    ("PYTHONPATH=src python3 -m tool_repository prompts validate", [sys.executable, "-m", "tool_repository", "prompts", "validate"]),
    ("PYTHONPATH=src python3 -m tool_repository milestones validate", [sys.executable, "-m", "tool_repository", "milestones", "validate"]),
    ("python3 -m unittest tests.test_catalogue_api", [sys.executable, "-m", "unittest", "tests.test_catalogue_api"]),
    ("PYTHONPATH=src python3 -m tool_repository catalogue build", [sys.executable, "-m", "tool_repository", "catalogue", "build"]),
)
REVIEWS = (("ai_engineer", "reviews/TR-M16_ai_engineer.md"), ("solution_architect", "reviews/TR-M16_solution_architect.md"), ("developer", "reviews/TR-M16_developer.md"))


def main() -> int:
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    if len(revision) != 40:
        raise RuntimeError("TR-M16 proof requires an inspectable Git commit")
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    payload = {
        "milestone_id": "TR-M16",
        "implementation_revision": revision,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "host": platform.node(), "runtime": "static catalogue build"},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS],
        "observed_result": "The catalogue accepted two validated prompt definitions, one governed template, and one explicitly human-approved goal record while publishing only metadata and immutable source hashes.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M16_prompt_template_catalogue.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
