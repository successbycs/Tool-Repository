"""Static validation for reusable prompt definitions and safe execution provenance."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, SchemaError


ROOT = Path(__file__).resolve().parents[2]
DEFINITION_SCHEMA_PATH = ROOT / "schemas" / "prompt-definition.schema.json"
EXECUTION_SCHEMA_PATH = ROOT / "schemas" / "prompt-execution.schema.json"
DEFAULT_DEFINITIONS_PATH = ROOT / "prompts" / "definitions"
_SENSITIVE_LITERAL = re.compile(r"(?:api[_-]?key|password|token|secret)\s*[:=]\s*\S+|authorization\s*:\s*bearer\s+\S+|bearer\s+[A-Za-z0-9._-]{10,}", re.I)
_FORBIDDEN_CONTENT_KEYS = {"rendered_prompt", "raw_prompt", "input", "output", "messages", "reasoning", "chain_of_thought", "credentials", "secrets"}


def _read_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON number {value}"))), []
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"{path}: cannot read JSON: {error}"]


def _validator(schema_path: Path) -> Draft202012Validator:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _schema_issues(payload: Any, schema_path: Path, label: str) -> list[str]:
    try:
        validator = _validator(schema_path)
    except (OSError, ValueError, json.JSONDecodeError, SchemaError) as error:
        return [f"{label} schema is invalid: {error}"]
    return [
        f"schema {'.'.join(str(part) for part in error.absolute_path) or label}: {error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: (list(item.absolute_path), item.message))
    ]


def _privacy_issues(value: Any, path: str = "record") -> list[str]:
    if isinstance(value, str):
        return [f"{path} appears to contain a secret literal"] if _SENSITIVE_LITERAL.search(value) else []
    if isinstance(value, list):
        return [issue for index, item in enumerate(value) for issue in _privacy_issues(item, f"{path}[{index}]")]
    if isinstance(value, dict):
        issues = [f"{path}.{key} must not store raw prompt, input, output, or reasoning content" for key in value if key in _FORBIDDEN_CONTENT_KEYS]
        return [*issues, *(issue for key, item in value.items() for issue in _privacy_issues(item, f"{path}.{key}"))]
    return []


def validate_prompt_definition(payload: Any) -> list[str]:
    """Validate one versioned reusable prompt definition without executing it."""

    issues = [*_schema_issues(payload, DEFINITION_SCHEMA_PATH, "prompt definition"), *_privacy_issues(payload, "prompt_definition")]
    if isinstance(payload, dict) and payload.get("data_classification") == "restricted":
        rendering = payload.get("rendering")
        if isinstance(rendering, dict) and rendering.get("execution_capture") != "protected_reference":
            issues.append("restricted prompt definitions must require protected_reference execution capture")
    return issues


def load_prompt_library(directory: Path = DEFAULT_DEFINITIONS_PATH) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    """Load static definitions and bind each identifier/version to its file hash."""

    if not directory.is_dir():
        return {}, [f"prompt definitions directory is missing: {directory}"]
    index: dict[tuple[str, str], dict[str, Any]] = {}
    issues: list[str] = []
    paths = sorted(directory.rglob("*.json"))
    if not paths:
        return {}, [f"prompt definitions directory contains no JSON definitions: {directory}"]
    for path in paths:
        payload, read_issues = _read_json(path)
        issues.extend(read_issues)
        if payload is None:
            continue
        definition_issues = validate_prompt_definition(payload)
        issues.extend(f"{path}: {issue}" for issue in definition_issues)
        if definition_issues or not isinstance(payload, dict):
            continue
        key = (payload["id"], payload["version"])
        if key in index:
            issues.append(f"duplicate prompt definition: {key[0]}@{key[1]}")
            continue
        index[key] = {"path": path, "payload": payload, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return index, issues


def validate_prompt_execution(payload: Any, definitions: dict[tuple[str, str], dict[str, Any]] | None = None) -> list[str]:
    """Validate a metadata-only execution record and its immutable prompt reference."""

    issues = [*_schema_issues(payload, EXECUTION_SCHEMA_PATH, "prompt execution"), *_privacy_issues(payload, "prompt_execution")]
    if not isinstance(payload, dict) or definitions is None:
        return issues
    prompt = payload.get("prompt")
    if not isinstance(prompt, dict):
        return issues
    key = (prompt.get("id"), prompt.get("version"))
    definition = definitions.get(key)
    if definition is None:
        issues.append("execution prompt id/version is not in the validated prompt library")
    elif prompt.get("definition_sha256") != definition["sha256"]:
        issues.append("execution prompt definition_sha256 does not match the validated definition bytes")
    return issues


def load_prompt_execution(path: Path, definitions: dict[tuple[str, str], dict[str, Any]] | None = None) -> tuple[dict[str, Any] | None, list[str]]:
    payload, issues = _read_json(path)
    if payload is None:
        return None, issues
    validation_issues = validate_prompt_execution(payload, definitions)
    return payload if isinstance(payload, dict) and not validation_issues else None, [*issues, *(f"{path}: {issue}" for issue in validation_issues)]
