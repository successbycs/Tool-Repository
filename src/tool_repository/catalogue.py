"""Static catalogue construction; it never imports or executes adapter code."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

from tool_repository.manifest import discover_manifests, load_manifest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "catalogue.schema.json"
RELEASE_INDEX_PATH = ROOT / "catalogue" / "release-index.json"
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_COMMIT = re.compile(r"^[a-f0-9]{40}$")
_TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")


def _read_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"{path}: cannot read JSON: {error}"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalogue_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_catalogue(payload: Any) -> list[str]:
    try:
        validator = _catalogue_validator()
    except (OSError, ValueError, json.JSONDecodeError, SchemaError) as error:
        return [f"published catalogue schema is invalid: {error}"]
    issues = [f"schema {'.'.join(str(part) for part in error.absolute_path) or 'catalogue'}: {error.message}" for error in validator.iter_errors(payload)]
    if not isinstance(payload, dict) or not isinstance(payload.get("adapters"), list):
        return issues
    keys: list[tuple[str, str]] = []
    for entry in payload["adapters"]:
        if isinstance(entry, dict) and isinstance(entry.get("adapter"), dict):
            adapter = entry["adapter"]
            if isinstance(adapter.get("id"), str) and isinstance(adapter.get("version"), str):
                keys.append((adapter["id"], adapter["version"]))
    if len(keys) != len(set(keys)):
        issues.append("catalogue contains duplicate adapter id/version entries")
    if keys != sorted(keys):
        issues.append("catalogue adapters must be sorted by id and version")
    return issues


def load_catalogue(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load and validate one generated catalogue document without adapter imports."""

    payload, issues = _read_json(path)
    if payload is None:
        return None, issues
    if not isinstance(payload, dict):
        return None, [*issues, f"{path}: catalogue must be an object"]
    return payload, [*issues, *validate_catalogue(payload)]


def _release_index_issues(index: Any) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    issues: list[str] = []
    records: dict[tuple[str, str], dict[str, Any]] = {}
    if not isinstance(index, dict) or set(index) != {"schema_version", "trusted_publishers", "releases"}:
        return records, ["release index must contain only schema_version, trusted_publishers, and releases"]
    if index.get("schema_version") != "1.0.0":
        issues.append("release index schema_version must be 1.0.0")
    publishers = index.get("trusted_publishers")
    if not isinstance(publishers, list) or not publishers or any(not isinstance(item, str) or not item.strip() for item in publishers) or len(set(publishers)) != len(publishers):
        issues.append("release index trusted_publishers must be a unique non-empty string list")
        publishers = []
    releases = index.get("releases")
    if not isinstance(releases, list) or not releases:
        return records, [*issues, "release index releases must be a non-empty list"]
    required = {"adapter_id", "adapter_version", "publisher", "release_tag", "release_commit", "artifact_uri", "manifest_sha256"}
    for position, release in enumerate(releases):
        label = f"release index releases[{position}]"
        if not isinstance(release, dict) or set(release) != required:
            issues.append(f"{label} has missing or unsupported fields")
            continue
        adapter_id, version = release["adapter_id"], release["adapter_version"]
        if not isinstance(adapter_id, str) or not _IDENTIFIER.fullmatch(adapter_id):
            issues.append(f"{label}.adapter_id is invalid")
        if not isinstance(version, str) or not _SEMVER.fullmatch(version):
            issues.append(f"{label}.adapter_version is invalid")
        if not isinstance(release["publisher"], str) or release["publisher"] not in publishers:
            issues.append(f"{label}.publisher is not trusted")
        if not isinstance(release["release_tag"], str) or not _TAG.fullmatch(release["release_tag"]):
            issues.append(f"{label}.release_tag is invalid")
        if not isinstance(release["release_commit"], str) or not _COMMIT.fullmatch(release["release_commit"]):
            issues.append(f"{label}.release_commit is invalid")
        if not isinstance(release["artifact_uri"], str) or not release["artifact_uri"].startswith("git+https://"):
            issues.append(f"{label}.artifact_uri must be an immutable Git HTTPS release reference")
        if not isinstance(release["manifest_sha256"], str) or not _SHA256.fullmatch(release["manifest_sha256"]):
            issues.append(f"{label}.manifest_sha256 is invalid")
        if isinstance(adapter_id, str) and isinstance(version, str):
            key = (adapter_id, version)
            if key in records:
                issues.append(f"duplicate release index entry for {adapter_id}@{version}")
            else:
                records[key] = release
    return records, issues


def build_catalogue(root: Path = ROOT, *, release_index_path: Path | None = None) -> tuple[dict[str, Any] | None, list[str]]:
    """Build a deterministic catalogue from static descriptor bytes and a release index."""

    root = root.resolve()
    index_path = (release_index_path or root / "catalogue" / "release-index.json").resolve()
    index, issues = _read_json(index_path)
    releases, index_issues = _release_index_issues(index)
    issues.extend(index_issues)
    if issues:
        return None, issues
    entries: list[dict[str, Any]] = []
    manifest_keys: set[tuple[str, str]] = set()
    for path in discover_manifests(root):
        manifest, manifest_issues = load_manifest(path, repository_root=root)
        issues.extend(manifest_issues)
        if manifest is None:
            continue
        adapter = manifest["adapter"]
        key = (adapter["id"], adapter["version"])
        manifest_keys.add(key)
        release = releases.get(key)
        if release is None:
            issues.append(f"no trusted immutable release entry exists for {adapter['id']}@{adapter['version']}")
            continue
        digest = _sha256(path)
        if release["manifest_sha256"] != digest:
            issues.append(f"release checksum mismatch for {adapter['id']}@{adapter['version']}")
            continue
        entries.append({
            "adapter": {field: adapter[field] for field in ("id", "version", "title", "summary", "status", "owner", "license")},
            "value": manifest["value"],
            "capabilities": manifest["capabilities"],
            "operations": manifest["operations"],
            "documentation": manifest["documentation"],
            "manifest_sha256": digest,
            "release": {field: release[field] for field in ("publisher", "release_tag", "release_commit", "artifact_uri")},
        })
    for adapter_id, version in sorted(set(releases) - manifest_keys):
        issues.append(f"release index contains no current descriptor for {adapter_id}@{version}")
    if issues:
        return None, issues
    payload = {"schema_version": "1.0.0", "release_index_sha256": _sha256(index_path), "adapters": sorted(entries, key=lambda item: (item["adapter"]["id"], item["adapter"]["version"]))}
    return payload, validate_catalogue(payload)


def write_catalogue(output_path: Path, root: Path = ROOT, *, release_index_path: Path | None = None) -> list[str]:
    payload, issues = build_catalogue(root, release_index_path=release_index_path)
    if issues or payload is None:
        return issues
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return []
