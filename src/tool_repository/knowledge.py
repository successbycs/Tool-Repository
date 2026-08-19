"""Static validation for adapter knowledge records with privacy controls."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, SchemaError


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "knowledge-record.schema.json"
_SENSITIVE_LITERAL = re.compile(r"(?:api[_-]?key|password|token|secret)\s*[:=]\s*\S+|authorization\s*:\s*bearer\s+\S+|bearer\s+[A-Za-z0-9._-]{10,}", re.I)


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _safe_repository_file(reference: Any, repository_root: Path) -> bool:
    if not isinstance(reference, str) or not reference.strip():
        return False
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    resolved_root = repository_root.resolve()
    resolved = (repository_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return False
    return resolved.is_file()


def _secret_issues(value: Any, path: str = "knowledge") -> list[str]:
    if isinstance(value, str):
        return [f"{path} appears to contain a secret literal"] if _SENSITIVE_LITERAL.search(value) else []
    if isinstance(value, list):
        return [issue for index, item in enumerate(value) for issue in _secret_issues(item, f"{path}[{index}]")]
    if isinstance(value, dict):
        return [issue for key, item in value.items() for issue in _secret_issues(item, f"{path}.{key}")]
    return []


def validate_knowledge_base(payload: Any, *, repository_root: Path | None = None, adapter_id: str | None = None, adapter_version: str | None = None) -> list[str]:
    """Validate clear separation between evidenced learning and suggestions."""

    issues: list[str] = []
    try:
        validator = _validator()
    except (OSError, json.JSONDecodeError, SchemaError) as error:
        return [f"published knowledge schema is invalid: {error}"]
    issues.extend(
        f"schema {'.'.join(str(part) for part in error.absolute_path) or 'knowledge'}: {error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: (list(item.absolute_path), item.message))
    )
    if not isinstance(payload, dict):
        return issues
    adapter = payload.get("adapter")
    if isinstance(adapter, dict):
        if adapter_id is not None and adapter.get("id") != adapter_id:
            issues.append("knowledge.adapter.id must match the referencing adapter descriptor")
        if adapter_version is not None and adapter.get("version") != adapter_version:
            issues.append("knowledge.adapter.version must match the referencing adapter descriptor")
    issues.extend(_secret_issues(payload))
    records = payload.get("records")
    if not isinstance(records, list):
        return issues
    identifiers: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        identifier = record.get("id")
        if isinstance(identifier, str):
            if identifier in identifiers:
                issues.append(f"duplicate knowledge record id: {identifier}")
            identifiers.add(identifier)
        if record.get("kind") == "validated_usage":
            reference = record.get("evidence_ref")
            if repository_root is None:
                issues.append(f"records[{index}].evidence_ref requires a repository root for admission validation")
            elif not _safe_repository_file(reference, repository_root):
                issues.append(f"records[{index}].evidence_ref must reference an existing repository-contained file")
            observed_on = record.get("observed_on")
            if isinstance(observed_on, str):
                try:
                    if date.fromisoformat(observed_on) > date.today():
                        issues.append(f"records[{index}].observed_on must not be in the future")
                except ValueError:
                    pass  # Draft 2020-12 format validation reports the structural error.
        elif record.get("kind") == "suggested_use":
            for prohibited in ("outcome", "observed_on", "evidence_ref"):
                if prohibited in record:
                    issues.append(f"records[{index}] suggested_use must not claim {prohibited}")
    return issues


def load_knowledge_base(path: Path, *, repository_root: Path | None = None, adapter_id: str | None = None, adapter_version: str | None = None) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON number {value}")))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"{path}: cannot read JSON: {error}"]
    issues = validate_knowledge_base(payload, repository_root=repository_root, adapter_id=adapter_id, adapter_version=adapter_version)
    return payload if isinstance(payload, dict) and not issues else None, [f"{path}: {issue}" for issue in issues]
