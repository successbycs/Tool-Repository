#!/usr/bin/env python3
"""Resolve and invoke the minimal solution's pinned T480 transport adapter."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


EXAMPLE_ROOT = Path(__file__).resolve().parent
REQUIRED_LOCK_FIELDS = {
    "kind", "adapter_id", "adapter_version", "publisher", "release_tag",
    "release_commit", "artifact_uri", "manifest_sha256",
}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def locked_adapter(lock_path: Path) -> dict[str, Any]:
    lock = read_json(lock_path)
    dependencies = lock.get("dependencies")
    if not isinstance(dependencies, list) or len(dependencies) != 1 or not isinstance(dependencies[0], dict):
        raise ValueError("minimal-solution lock must contain exactly one adapter dependency")
    dependency = dependencies[0]
    if set(dependency) != REQUIRED_LOCK_FIELDS:
        raise ValueError("minimal-solution lock has missing or unsupported dependency fields")
    if dependency["kind"] != "adapter" or dependency["adapter_id"] != "t480-transport":
        raise ValueError("minimal-solution lock must select t480-transport")
    return dependency


def resolve_catalogue_entry(catalogue_path: Path, lock_path: Path) -> dict[str, Any]:
    catalogue = read_json(catalogue_path)
    lock = read_json(lock_path)
    expected_index_hash = lock.get("catalogue", {}).get("release_index_sha256") if isinstance(lock.get("catalogue"), dict) else None
    if catalogue.get("release_index_sha256") != expected_index_hash:
        raise ValueError("catalogue release-index hash does not match the solution lock")
    dependency = locked_adapter(lock_path)
    entries = catalogue.get("adapters")
    if not isinstance(entries, list):
        raise ValueError("catalogue adapters must be a list")
    matches = [
        entry for entry in entries
        if isinstance(entry, dict)
        and isinstance(entry.get("adapter"), dict)
        and entry["adapter"].get("id") == dependency["adapter_id"]
        and entry["adapter"].get("version") == dependency["adapter_version"]
    ]
    if len(matches) != 1:
        raise ValueError("locked adapter is absent or ambiguous in the catalogue")
    entry = matches[0]
    release = entry.get("release")
    if not isinstance(release, dict):
        raise ValueError("catalogue adapter release must be an object")
    for field in ("publisher", "release_tag", "release_commit", "artifact_uri"):
        if release.get(field) != dependency[field]:
            raise ValueError(f"catalogue {field} does not match the solution lock")
    if entry.get("manifest_sha256") != dependency["manifest_sha256"]:
        raise ValueError("catalogue descriptor hash does not match the solution lock")
    return dependency


def verify_pinned_checkout(repository_root: Path, dependency: dict[str, Any]) -> None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root, text=True, capture_output=True, check=False
    )
    if result.returncode != 0 or result.stdout.strip() != dependency["release_commit"]:
        raise ValueError("Tool Repository checkout is not at the locked release commit")
    descriptor = repository_root / "adapters" / dependency["adapter_id"] / "adapter.json"
    digest = hashlib.sha256(descriptor.read_bytes()).hexdigest()
    if digest != dependency["manifest_sha256"]:
        raise ValueError("Tool Repository descriptor hash does not match the solution lock")


def load_adapter(repository_root: Path):
    source = repository_root / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    path = repository_root / "adapters" / "t480-transport" / "transport.py"
    spec = importlib.util.spec_from_file_location("minimal_solution_t480_transport", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load locked t480-transport adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.T480TransportAdapter()


def consume(repository_root: Path, catalogue_path: Path, lock_path: Path, target: str) -> dict[str, Any]:
    dependency = resolve_catalogue_entry(catalogue_path, lock_path)
    verify_pinned_checkout(repository_root, dependency)
    result = load_adapter(repository_root).invoke("validate_target", {"target": target}, config={"target": target})
    if not result.success:
        raise ValueError(result.error["message"] if result.error else "locked adapter failed")
    return {"adapter": f"{dependency['adapter_id']}@{dependency['adapter_version']}", "release_commit": dependency["release_commit"], "result": result.output}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool-repository", type=Path, required=True, help="local checkout at the exact locked commit")
    parser.add_argument("--catalogue", type=Path, required=True, help="downloaded read-only catalogue JSON")
    parser.add_argument("--lock", type=Path, default=EXAMPLE_ROOT / "tool-repository.lock.json")
    parser.add_argument("--target", default="operator@t480")
    args = parser.parse_args()
    print(json.dumps(consume(args.tool_repository.resolve(), args.catalogue.resolve(), args.lock.resolve(), args.target), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
