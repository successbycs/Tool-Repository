#!/usr/bin/env python3
"""Verify the local CS AI Lab host and, optionally, its installed release."""

from __future__ import annotations

import argparse
import json
import os
import platform
import pwd
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve_tag(source: Path, release: str) -> str | None:
    result = subprocess.run(["git", "-C", str(source), "rev-parse", "--verify", f"{release}^{{commit}}"], text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--account", default=pwd.getpwuid(os.geteuid()).pw_name)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--install-root", type=Path)
    args = parser.parse_args()

    issues: list[str] = []
    actual_host = platform.node()
    actual_account = pwd.getpwuid(os.geteuid()).pw_name
    if args.host.casefold() != actual_host.casefold():
        issues.append("host identity does not match")
    if args.account != actual_account:
        issues.append("non-root deployment account does not match")
    if os.geteuid() == 0:
        issues.append("deployment must not use root")
    commit = resolve_tag(args.source, args.release)
    if commit is None:
        issues.append("release tag does not resolve to an inspectable commit")
    installed_release: dict[str, object] | None = None
    if args.install_root is not None:
        current = args.install_root / "current"
        metadata = current / "release.json"
        if not current.is_symlink() or not metadata.is_file():
            issues.append("current immutable release metadata is missing")
        else:
            try:
                installed_release = json.loads(metadata.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                issues.append("current immutable release metadata is invalid")
            else:
                if installed_release.get("release_tag") != args.release or installed_release.get("commit") != commit:
                    issues.append("installed release does not match requested tag and commit")
                environment = {**os.environ, "PYTHONPATH": str(current / "src")}
                check = subprocess.run([sys.executable, "-m", "tool_repository", "validate", "--require-knowledge"], cwd=current, env=environment, text=True, capture_output=True, check=False)
                if check.returncode != 0:
                    issues.append("installed release static validation failed")
    payload = {"ready": not issues, "expected_host": args.host, "actual_host": actual_host, "expected_account": args.account, "actual_account": actual_account, "release": args.release, "commit": commit, "installed_release": installed_release, "issues": issues}
    print(json.dumps(payload, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
