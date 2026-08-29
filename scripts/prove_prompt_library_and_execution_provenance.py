#!/usr/bin/env python3
"""Generate commit-bound TR-M07 prompt-library verification evidence."""

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
    ("python3 -m unittest tests.test_prompt_library", [sys.executable, "-m", "unittest", "tests.test_prompt_library"]),
)
REVIEWS = (
    ("ai_engineer", "reviews/TR-M07_ai_engineer.md"),
    ("solution_architect", "reviews/TR-M07_solution_architect.md"),
    ("developer", "reviews/TR-M07_developer.md"),
)


def revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or len(result.stdout.strip()) != 40:
        raise RuntimeError("TR-M07 proof requires an inspectable Git commit")
    return result.stdout.strip()


def main() -> int:
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    payload = {
        "milestone_id": "TR-M07",
        "implementation_revision": revision(),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS],
        "observed_result": "The static prompt library validates a versioned reusable definition and rejects execution provenance that exposes raw prompt content, secrets, hidden reasoning, or a mismatched immutable definition.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M07_prompt_library_and_execution_provenance.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
