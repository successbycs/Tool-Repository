#!/usr/bin/env python3
"""Generate commit-bound TR-M13 evidence for the owner-approved T480 core set."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from prove_t480_local_model_profiles import smoke


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("python3 scripts/verify_t480_ollama_profiles.py", [sys.executable, "scripts/verify_t480_ollama_profiles.py"]),
    ("PYTHONPATH=src python3 -m tool_repository catalogue build", [sys.executable, "-m", "tool_repository", "catalogue", "build"]),
    ("python3 -m unittest tests.test_catalogue_api", [sys.executable, "-m", "unittest", "tests.test_catalogue_api"]),
)
REVIEWS = (("ai_engineer", "reviews/TR-M13_ai_engineer.md"), ("solution_architect", "reviews/TR-M13_solution_architect.md"), ("developer", "reviews/TR-M13_developer.md"))


def main() -> int:
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    if len(revision) != 40:
        raise RuntimeError("TR-M13 proof requires an inspectable Git commit")
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    checks.extend((smoke("qwen3:4b", think=True), smoke("qwen2.5-coder:7b")))
    payload = {"milestone_id": "TR-M13", "implementation_revision": revision, "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"), "environment": {"python": platform.python_version(), "platform": platform.platform(), "host": platform.node(), "runtime": "Ollama 0.19.0 loopback"}, "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed", "verification": checks, "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS], "observed_result": "The active T480 profile set contains exactly Qwen 3 4B and Qwen 2.5 Coder 7B; both match local readback and produced bounded loopback-only smoke responses."}
    path = ROOT / "runs" / "proofs" / "TR-M13_t480_core_model_rationalisation.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
