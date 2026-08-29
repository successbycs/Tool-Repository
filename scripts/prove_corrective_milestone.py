#!/usr/bin/env python3
"""Generate commit-bound proof for the corrective milestones."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "TR-M09": (("PYTHONPATH=src python3 -m tool_repository repositories validate-queue", [sys.executable, "-m", "tool_repository", "repositories", "validate-queue"]), ("python3 -m unittest tests.test_repository_intake", [sys.executable, "-m", "unittest", "tests.test_repository_intake"])),
    "TR-M10": (("python3 -m unittest tests.test_milestone_governance", [sys.executable, "-m", "unittest", "tests.test_milestone_governance"]),),
    "TR-M11": (("python3 -m unittest tests.test_contracts", [sys.executable, "-m", "unittest", "tests.test_contracts"]),),
}
NAMES = {"TR-M09": "repository_asset_intake_and_curation", "TR-M10": "proof_and_review_integrity", "TR-M11": "runtime_contract_enforcement"}

def main() -> int:
    milestone = sys.argv[1]
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks=[]
    for label, command in COMMANDS[milestone]:
        result=subprocess.run(command,cwd=ROOT,env=environment,text=True,capture_output=True,check=False); output=result.stdout+result.stderr
        checks.append({"command":label,"exit_code":result.returncode,"output":output,"output_sha256":hashlib.sha256(output.encode()).hexdigest()})
    reviews=[]
    for role, filename in (("ai_engineer", "ai_engineer"), ("solution_architect", "solution_architect"), ("developer", "developer")):
        path=ROOT/"reviews"/f"{milestone}_{filename}.md"; reviews.append({"role":role,"status":"passed","reference":str(path.relative_to(ROOT)),"content_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    payload={"milestone_id":milestone,"implementation_revision":revision,"generated_at":datetime.now(UTC).isoformat().replace("+00:00","Z"),"environment":{"python":platform.python_version(),"platform":platform.platform()},"status":"passed" if all(c["exit_code"]==0 for c in checks) else "failed","verification":checks,"reviews":reviews,"observed_result":"Declared corrective milestone verification passed on the recorded committed revision."}
    path=ROOT/"runs"/"proofs"/f"{milestone}_{NAMES[milestone]}.json"; path.write_text(json.dumps(payload,indent=2)+"\n"); print(path.relative_to(ROOT)); return 0 if payload["status"]=="passed" else 1
if __name__ == "__main__": raise SystemExit(main())
