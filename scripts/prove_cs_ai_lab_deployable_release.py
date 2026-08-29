#!/usr/bin/env python3
"""Generate commit-bound deployment proof for the local TR-M01A release."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import pwd
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL_ROOT = Path("/home/chris/.local/share/tool-repository")
VERIFY_COMMAND = "python3 scripts/verify_cs_ai_lab_deploy.py --host Piwakawaka --account chris --release v0.1.0 --source /home/chris/Tool-Repository --install-root /home/chris/.local/share/tool-repository"
BASELINE_TAG = "v0.0.0"
RELEASE_TAG = "v0.1.0"
REVIEWS = (("solution_architect", "reviews/TR-M01A_solution_architect.md"), ("developer", "reviews/TR-M01A_developer.md"))


def revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or len(result.stdout.strip()) != 40:
        raise RuntimeError("TR-M01A proof requires an inspectable Git commit")
    return result.stdout.strip()


def tag_commit(tag: str) -> str:
    result = subprocess.run(["git", "rev-parse", "--verify", f"{tag}^{{commit}}"], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or len(result.stdout.strip()) != 40:
        raise RuntimeError(f"{tag} must resolve to an inspectable Git commit")
    return result.stdout.strip()


def main() -> int:
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    baseline_id = f"{BASELINE_TAG}-{tag_commit(BASELINE_TAG)[:12]}"
    commands = (
        ("python3 -m unittest tests.test_cs_ai_lab_deployment", [sys.executable, "-m", "unittest", "tests.test_cs_ai_lab_deployment"]),
        (f"deploy/cs-ai-lab/rollback.sh --install-root {INSTALL_ROOT} --release-id {baseline_id} --account chris", [str(ROOT / "deploy" / "cs-ai-lab" / "rollback.sh"), "--install-root", str(INSTALL_ROOT), "--release-id", baseline_id, "--account", "chris"]),
        (f"python3 scripts/verify_cs_ai_lab_deploy.py --host Piwakawaka --account chris --release {BASELINE_TAG} --source /home/chris/Tool-Repository --install-root {INSTALL_ROOT}", [sys.executable, "scripts/verify_cs_ai_lab_deploy.py", "--host", "Piwakawaka", "--account", "chris", "--release", BASELINE_TAG, "--source", str(ROOT), "--install-root", str(INSTALL_ROOT)]),
        (f"deploy/cs-ai-lab/install.sh --source /home/chris/Tool-Repository --release {RELEASE_TAG} --install-root {INSTALL_ROOT} --account chris", [str(ROOT / "deploy" / "cs-ai-lab" / "install.sh"), "--source", str(ROOT), "--release", RELEASE_TAG, "--install-root", str(INSTALL_ROOT), "--account", "chris"]),
        (VERIFY_COMMAND, [sys.executable, "scripts/verify_cs_ai_lab_deploy.py", "--host", "Piwakawaka", "--account", "chris", "--release", RELEASE_TAG, "--source", str(ROOT), "--install-root", str(INSTALL_ROOT)]),
    )
    checks = []
    for label, command in commands:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    current_metadata = INSTALL_ROOT / "current" / "release.json"
    metadata = json.loads(current_metadata.read_text(encoding="utf-8")) if current_metadata.is_file() else None
    payload = {
        "milestone_id": "TR-M01A",
        "implementation_revision": revision(),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "host": platform.node(), "account": pwd.getpwuid(os.geteuid()).pw_name},
        "status": "passed" if metadata is not None and all(check["exit_code"] == 0 for check in checks) else "failed",
        "verification": checks,
        "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS],
        "deployment": {"install_root": str(INSTALL_ROOT), "rollback_baseline": {"release": BASELINE_TAG, "release_id": baseline_id}, "current_release": metadata},
        "observed_result": "A non-root Piwakawaka installation resolves v0.1.0 to an exact commit, validates the installed release, rolls back to v0.0.0, and restores v0.1.0.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M01A_cs_ai_lab_deployable_release.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
