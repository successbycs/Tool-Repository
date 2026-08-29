"""Read-only validation for one-repository-at-a-time asset intake."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, SchemaError


ROOT = Path(__file__).resolve().parents[2]
QUEUE_SCHEMA_PATH = ROOT / "schemas" / "repository-intake.schema.json"
_SENSITIVE_LITERAL = re.compile(r"(?:api[_-]?key|password|token|secret)\s*[:=]\s*\S+|authorization\s*:\s*bearer\s+\S+", re.I)


def _validator() -> Draft202012Validator:
    schema = json.loads(QUEUE_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _safe_file(root: Path, reference: Any) -> Path | None:
    if not isinstance(reference, str) or not reference.strip():
        return None
    path = Path(reference)
    if path.is_absolute() or ".." in path.parts:
        return None
    resolved_root = root.resolve()
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved if resolved.is_file() else None


def _schema_issues(payload: Any) -> list[str]:
    try:
        validator = _validator()
    except (OSError, ValueError, json.JSONDecodeError, SchemaError) as error:
        return [f"published repository intake schema is invalid: {error}"]
    return [
        f"schema {'.'.join(str(part) for part in error.absolute_path) or 'intake'}: {error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: (list(item.absolute_path), item.message))
    ]


def _secret_issues(value: Any, path: str = "intake") -> list[str]:
    if isinstance(value, str):
        return [f"{path} appears to contain a secret literal"] if _SENSITIVE_LITERAL.search(value) else []
    if isinstance(value, list):
        return [issue for index, item in enumerate(value) for issue in _secret_issues(item, f"{path}[{index}]")]
    if isinstance(value, dict):
        return [issue for key, item in value.items() for issue in _secret_issues(item, f"{path}.{key}")]
    return []


def validate_queue(payload: Any, *, repository_root: Path = ROOT) -> list[str]:
    """Validate a queue without inspecting, importing, or executing source code."""

    issues = _schema_issues(payload)
    if not isinstance(payload, dict):
        return issues
    sources = payload.get("sources")
    if not isinstance(sources, list):
        return issues
    active = [item for item in sources if isinstance(item, dict) and item.get("status") == "assessing"]
    if len(active) != 1:
        issues.append("intake queue must contain exactly one source with status assessing")
    seen: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            continue
        identifier = source.get("id")
        if isinstance(identifier, str):
            if identifier in seen:
                issues.append(f"duplicate intake source id: {identifier}")
            seen.add(identifier)
        if source.get("status") == "assessing":
            assessment = _safe_file(repository_root, source.get("assessment"))
            if assessment is None:
                issues.append(f"sources[{index}].assessment must reference an existing repository-contained file")
            else:
                assessment_payload, assessment_issues = load_assessment(assessment, repository_root=repository_root)
                issues.extend(assessment_issues)
                if isinstance(assessment_payload, dict):
                    identity = assessment_payload.get("source")
                    if not isinstance(identity, dict) or identity.get("id") != identifier:
                        issues.append(f"sources[{index}].assessment source.id must match the queue source")
                    elif identity.get("revision") != source.get("revision"):
                        issues.append(f"sources[{index}].assessment source.revision must match the queue source")
    return issues


def validate_assessment(payload: Any, *, repository_root: Path = ROOT) -> list[str]:
    # The shared file contains both schema definitions; assessment validation uses its named definition.
    try:
        schema = json.loads(QUEUE_SCHEMA_PATH.read_text(encoding="utf-8"))
        assessment_schema = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/assessment"}
        Draft202012Validator.check_schema(assessment_schema)
        validator = Draft202012Validator(assessment_schema, format_checker=FormatChecker())
        issues = [
            f"assessment {'.'.join(str(part) for part in error.absolute_path) or 'root'}: {error.message}"
            for error in sorted(validator.iter_errors(payload), key=lambda item: (list(item.absolute_path), item.message))
        ]
    except (OSError, ValueError, json.JSONDecodeError, KeyError, SchemaError) as error:
        return [f"published repository intake assessment schema is invalid: {error}"]
    issues.extend(_secret_issues(payload, "assessment"))
    if not isinstance(payload, dict):
        return issues
    source = payload.get("source")
    if isinstance(source, dict) and source.get("license_status") != "confirmed":
        for candidate in payload.get("candidates", []):
            if isinstance(candidate, dict) and candidate.get("decision") in {"adopt", "extract"}:
                issues.append("unresolved licence/provenance requires candidates to be rewrite, defer, reference_only, or reject")
                break
    for index, candidate in enumerate(payload.get("candidates", [])):
        if not isinstance(candidate, dict):
            continue
        decision = candidate.get("decision")
        if decision in {"adopt", "extract"} and not candidate.get("acceptance_checks"):
            issues.append(f"candidates[{index}] promotion decisions require acceptance checks")
    return issues


def load_queue(path: Path, *, repository_root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON number {value}")))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"{path}: cannot read JSON: {error}"]
    issues = validate_queue(payload, repository_root=repository_root)
    return payload if isinstance(payload, dict) and not issues else None, [f"{path}: {issue}" for issue in issues]


def load_assessment(path: Path, *, repository_root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON number {value}")))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"{path}: cannot read JSON: {error}"]
    issues = validate_assessment(payload, repository_root=repository_root)
    return payload if isinstance(payload, dict) and not issues else None, [f"{path}: {issue}" for issue in issues]
