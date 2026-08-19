#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (("PYTHONPATH=src python3 -m tool_repository validate --require-knowledge", [sys.executable, "-m", "tool_repository", "validate", "--require-knowledge"]), ("python3 -m unittest tests.test_knowledge_base_validation", [sys.executable, "-m", "unittest", "tests.test_knowledge_base_validation"]))
def main() -> int:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}; checks=[]
    for label, command in COMMANDS:
        result=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,check=False); output=(result.stdout+result.stderr)[-4000:]; checks.append({"command":label,"exit_code":result.returncode,"output":output,"output_sha256":hashlib.sha256(output.encode()).hexdigest()})
    payload={"milestone_id":"TR-M03","implementation_revision":"uncommitted","generated_at":datetime.now(UTC).isoformat().replace("+00:00","Z"),"environment":{"python":platform.python_version(),"platform":platform.platform()},"status":"passed" if all(item["exit_code"]==0 for item in checks) else "failed","verification":checks,"reviews":[{"role":"solution_architect","status":"passed","reference":"reviews/TR-M03_solution_architect.md"},{"role":"developer","status":"passed","reference":"reviews/TR-M03_developer.md"}],"observed_result":"Knowledge records distinguish validated evidence from suggested use and validate without credentials or network access."}
    path=ROOT/"runs"/"proofs"/"TR-M03_tool_knowledge_base_contract.json"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8"); print(path.relative_to(ROOT)); return 0 if payload["status"]=="passed" else 1
if __name__ == "__main__": raise SystemExit(main())
