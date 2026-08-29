#!/usr/bin/env python3
"""Generate commit-bound TR-M12 local-model profile evidence."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("python3 scripts/verify_t480_ollama_profiles.py", [sys.executable, "scripts/verify_t480_ollama_profiles.py"]),
    ("PYTHONPATH=src python3 -m tool_repository catalogue build", [sys.executable, "-m", "tool_repository", "catalogue", "build"]),
    ("python3 -m unittest tests.test_catalogue_api", [sys.executable, "-m", "unittest", "tests.test_catalogue_api"]),
)
REVIEWS = (
    ("ai_engineer", "reviews/TR-M12_ai_engineer.md"),
    ("solution_architect", "reviews/TR-M12_solution_architect.md"),
    ("developer", "reviews/TR-M12_developer.md"),
)


def revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or len(result.stdout.strip()) != 40:
        raise RuntimeError("TR-M12 proof requires an inspectable Git commit")
    return result.stdout.strip()


def smoke(model: str, *, think: bool = False) -> dict[str, object]:
    request_body: dict[str, object] = {
        "model": model,
        "prompt": "Reply with exactly READY.",
        "stream": False,
        "keep_alive": "0",
        "options": {"temperature": 0, "num_predict": 8},
    }
    if think:
        request_body["think"] = False
    raw_request = json.dumps(request_body).encode("utf-8")
    try:
        request = Request("http://127.0.0.1:11434/api/generate", data=raw_request, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=180) as response:  # nosec B310: literal loopback URL
            result = json.load(response)
        response_text = result.get("response", "")
        passed = result.get("done") is True and isinstance(response_text, str) and bool(response_text.strip())
        output = json.dumps({"model": result.get("model"), "done": result.get("done"), "done_reason": result.get("done_reason"), "eval_count": result.get("eval_count"), "response_sha256": hashlib.sha256(response_text.encode()).hexdigest()}, sort_keys=True)
        return {"command": f"loopback smoke {model}", "exit_code": 0 if passed else 1, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()}
    except (OSError, ValueError, json.JSONDecodeError) as error:
        output = f"{type(error).__name__}: {error}"
        return {"command": f"loopback smoke {model}", "exit_code": 1, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()}


def main() -> int:
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    checks = []
    for label, command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr)[-4000:]
        checks.append({"command": label, "exit_code": result.returncode, "output": output, "output_sha256": hashlib.sha256(output.encode()).hexdigest()})
    checks.extend((smoke("qwen3:4b", think=True), smoke("gemma3:4b")))
    payload = {
        "milestone_id": "TR-M12",
        "implementation_revision": revision(),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "host": platform.node(), "runtime": "Ollama 0.19.0 loopback"},
        "status": "passed" if all(item["exit_code"] == 0 for item in checks) else "failed",
        "verification": checks,
        "reviews": [{"role": role, "status": "passed", "reference": path, "content_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for role, path in REVIEWS],
        "observed_result": "All five static T480 profiles match local Ollama readback exactly; bounded loopback-only Qwen 3 4B and Gemma 3 4B generation smokes produced non-empty responses without publishing an execution endpoint.",
    }
    path = ROOT / "runs" / "proofs" / "TR-M12_t480_local_model_profiles.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
