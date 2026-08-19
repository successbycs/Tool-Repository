#!/usr/bin/env python3
"""Validate the repository governance and importable shared contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.milestones import validate_registry
from tool_repository.policy_validation import validate_policy_docs


def main() -> int:
    issues = [*validate_policy_docs(ROOT), *validate_registry(ROOT)]
    try:
        from tool_repository.contracts import Adapter, AdapterResult, OperationDefinition
        assert Adapter and AdapterResult and OperationDefinition
    except Exception as error:  # pragma: no cover - command-line failure path
        issues.append(f"shared adapter contract could not be imported: {error}")
    if issues:
        print("\n".join(f"ERROR: {issue}" for issue in issues))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
