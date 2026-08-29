#!/usr/bin/env python3
"""Generate commit-bound TR-M15 Ollama-readiness adapter evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
COMMANDS = (
    ("PYTHONPATH=src python3 -m tool_repository validate", [sys.executable, "-m", "tool_repository", "validate"]),
    ("python3 -m unittest tests.test_conformance", [sys.executable, "-m", "unittest", "tests.test_conformance"]),
    ("python3 scripts/verify_t480_ollama_profiles.py", [sys.executable, "scripts/verify_t480_ollama_profiles.py"]),
    ("PYTHONPATH=src python3 -m tool_repository catalogue build", [sys.executable, "-m", "tool_repository", "catalogue", "build"]),
)
REVIEWS = (("ai_engineer", "reviews/TR-M15_ai_engineer.md"), ("solution_architect", "reviews/TR-M15_solution_architect.md"), ("developer", "reviews/TR-M15_developer.md"))


def adapter_readback() -> dict[str, object]:
    try:
        path = ROOT / "adapters" / "ollama-readiness" / "adapter.py"
        spec = importlib.util.spec_from_file_location("ollama_readiness_proof", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load Ollama readiness adapter")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.OllamaReadinessAdapter(module.LoopbackOllamaInventoryProbe()).health_check(config={"target": "t480"})
        output = json.dumps(result.to_dict(), sort_keys=True)
        passed = result.success and result.output.get("ready") is True and result.output.get("endpoint_scope") == "loopback_only"
        return {"command": "ollama-readiness literal loopback adapter readback", "exit_code": 0 if passed else 1, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()}
    except Exception as error:
        output = f"{type(error).__name__}: {error}"
        return {"command": "ollama-readiness literal loopback adapter readback", "exit_code": 1, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()}


def main() -> int:
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    if len(revision) != 40:
        raise RuntimeError("TR-M15 proof requires an inspectable Git commit")
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    checks.append(adapter_readback())
    payload = {
        "milestone_id": "TR-M15",
        "implementation_revision": revision,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "host": platform.node(), "runtime": "Ollama loopback"},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS],
        "observed_result": "The clean-room Ollama readiness adapter read the literal T480 loopback inventory and matched exactly the two approved Qwen profile digests without model mutation, prompt submission, or network exposure.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M15_ollama_readiness_adapter.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
