"""Static validation for canonical adapter descriptors; no adapter code is imported."""

from __future__ import annotations

import json
import re
from math import isfinite
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

from tool_repository.contracts import CONTRACT_VERSION

SCHEMA_VERSION = "1.0.0"
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "adapter.schema.json"
_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_OPERATION = re.compile(r"^[a-z][a-z0-9_]*$")
_CAPABILITY = re.compile(r"^[a-z][a-z0-9_-]*$")
_SECRET = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object(value: Any, label: str, issues: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        issues.append(f"{label} must be an object")
        return None
    return value


def _required(obj: dict[str, Any], keys: set[str], label: str, issues: list[str]) -> None:
    missing = keys - set(obj)
    if missing:
        issues.append(f"{label} missing required fields: {', '.join(sorted(missing))}")


def _no_extra(obj: dict[str, Any], allowed: set[str], label: str, issues: list[str]) -> None:
    extras = set(obj) - allowed
    if extras:
        issues.append(f"{label} has unsupported fields: {', '.join(sorted(extras))}")


def _string_list(value: Any, label: str, issues: list[str]) -> None:
    if not isinstance(value, list) or not value or any(not _nonempty_string(item) for item in value):
        issues.append(f"{label} must be a non-empty list of non-empty strings")


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    version = schema["properties"]["adapter"]["properties"]["contract_version"].get("const")
    if version != CONTRACT_VERSION:
        raise RuntimeError("adapter schema contract version does not match the shared adapter contract")
    return Draft202012Validator(schema)


def _schema_issues(manifest: Any) -> list[str]:
    try:
        validator = _validator()
    except (OSError, json.JSONDecodeError, SchemaError, KeyError, RuntimeError) as error:
        return [f"published adapter schema is invalid: {error}"]
    return [
        f"schema {'.'.join(str(part) for part in error.absolute_path) or 'manifest'}: {error.message}"
        for error in sorted(validator.iter_errors(manifest), key=lambda item: (list(item.absolute_path), item.message))
    ]


def _embedded_schema_issues(schema: Any, label: str) -> list[str]:
    if not isinstance(schema, dict):
        return []
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        return [f"{label} must be a valid Draft 2020-12 JSON Schema: {error.message}"]
    return []


def _secret_values_in_schema(schema: Any, secret_names: set[str], path: str = "configuration.schema", sensitive: bool = False) -> list[str]:
    """Reject literals on declared or credential-like configuration fields."""

    issues: list[str] = []
    if isinstance(schema, dict):
        if sensitive:
            for key in {"default", "const", "example", "examples", "enum"} & set(schema):
                issues.append(f"{path}.{key} must not contain a secret value")
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                for property_name, property_schema in value.items():
                    normalized = re.sub(r"[^a-z0-9]", "", property_name.lower())
                    looks_secret = bool(re.search(r"(secret|token|password|credential|apikey|api_key)", property_name, re.I))
                    issues.extend(_secret_values_in_schema(property_schema, secret_names, f"{path}.properties.{property_name}", sensitive or looks_secret or normalized in secret_names))
            else:
                issues.extend(_secret_values_in_schema(value, secret_names, f"{path}.{key}", sensitive))
    elif isinstance(schema, list):
        for index, value in enumerate(schema):
            issues.extend(_secret_values_in_schema(value, secret_names, f"{path}[{index}]", sensitive))
    return issues


def validate_manifest(manifest: Any, *, repository_root: Path | None = None) -> list[str]:
    """Return deterministic validation errors for a descriptor object."""

    issues: list[str] = _schema_issues(manifest)
    root = _object(manifest, "manifest", issues)
    if root is None:
        return issues
    required = {"schema_version", "adapter", "value", "provenance", "capabilities", "operations", "configuration", "safety", "health_check", "documentation"}
    _required(root, required, "manifest", issues)
    _no_extra(root, required, "manifest", issues)
    if root.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION}")

    adapter = _object(root.get("adapter"), "adapter", issues)
    if adapter is not None:
        fields = {"id", "version", "contract_version", "title", "summary", "status", "owner", "license"}
        _required(adapter, fields, "adapter", issues); _no_extra(adapter, fields, "adapter", issues)
        if not _nonempty_string(adapter.get("id")) or not _IDENTIFIER.fullmatch(adapter.get("id", "")):
            issues.append("adapter.id must be a lowercase stable identifier")
        if not _nonempty_string(adapter.get("version")) or not _SEMVER.fullmatch(adapter.get("version", "")):
            issues.append("adapter.version must be SemVer")
        if adapter.get("contract_version") != CONTRACT_VERSION:
            issues.append(f"adapter.contract_version must be {CONTRACT_VERSION}")
        for key in ("title", "summary", "owner", "license"):
            if not _nonempty_string(adapter.get(key)):
                issues.append(f"adapter.{key} must be a non-empty string")
        if adapter.get("status") not in {"draft", "active", "deprecated", "archived"}:
            issues.append("adapter.status is invalid")

    value = _object(root.get("value"), "value", issues)
    if value is not None:
        fields = {"use_cases", "fit_for", "not_for", "limitations"}
        _required(value, fields, "value", issues); _no_extra(value, fields, "value", issues)
        for key in fields: _string_list(value.get(key), f"value.{key}", issues)

    provenance = _object(root.get("provenance"), "provenance", issues)
    if provenance is not None:
        fields = {"origin", "changed_from"}
        _required(provenance, fields, "provenance", issues); _no_extra(provenance, fields, "provenance", issues)
        origin = _object(provenance.get("origin"), "provenance.origin", issues)
        if origin is not None:
            fields = {"source", "revision", "license", "owner"}
            _required(origin, fields, "provenance.origin", issues); _no_extra(origin, fields, "provenance.origin", issues)
            for key in fields:
                if not _nonempty_string(origin.get(key)):
                    issues.append(f"provenance.origin.{key} must be a non-empty string")
        if not isinstance(provenance.get("changed_from"), str):
            issues.append("provenance.changed_from must be a string")

    capabilities = root.get("capabilities")
    names: set[str] = set()
    if not isinstance(capabilities, list) or not capabilities:
        issues.append("capabilities must be a non-empty list")
    else:
        for index, item in enumerate(capabilities):
            capability = _object(item, f"capabilities[{index}]", issues)
            if capability is None: continue
            _required(capability, {"name", "description"}, f"capabilities[{index}]", issues); _no_extra(capability, {"name", "description"}, f"capabilities[{index}]", issues)
            name = capability.get("name")
            if not _nonempty_string(name) or not _CAPABILITY.fullmatch(name): issues.append(f"capabilities[{index}].name is invalid")
            elif name in names: issues.append(f"duplicate capability name: {name}")
            else: names.add(name)
            if not _nonempty_string(capability.get("description")): issues.append(f"capabilities[{index}].description must be a non-empty string")

    operations = root.get("operations")
    operation_names: set[str] = set()
    if not isinstance(operations, list) or not operations:
        issues.append("operations must be a non-empty list")
    else:
        for index, item in enumerate(operations):
            operation = _object(item, f"operations[{index}]", issues)
            if operation is None: continue
            fields = {"name", "summary", "capability", "input_schema", "output_schema", "side_effect", "idempotency", "timeout_seconds", "retry_guidance"}
            _required(operation, fields, f"operations[{index}]", issues); _no_extra(operation, fields, f"operations[{index}]", issues)
            name = operation.get("name")
            if not _nonempty_string(name) or not _OPERATION.fullmatch(name): issues.append(f"operations[{index}].name is invalid")
            elif name in operation_names: issues.append(f"duplicate operation name: {name}")
            else: operation_names.add(name)
            if not _nonempty_string(operation.get("summary")): issues.append(f"operations[{index}].summary must be a non-empty string")
            if operation.get("capability") not in names: issues.append(f"operations[{index}].capability must name a declared capability")
            for key in ("input_schema", "output_schema"):
                if not isinstance(operation.get(key), dict): issues.append(f"operations[{index}].{key} must be an object")
                issues.extend(_embedded_schema_issues(operation.get(key), f"operations[{index}].{key}"))
            if operation.get("side_effect") not in {"read_only", "mutating", "destructive"}: issues.append(f"operations[{index}].side_effect is invalid")
            if operation.get("idempotency") not in {"idempotent", "non_idempotent", "unknown"}: issues.append(f"operations[{index}].idempotency is invalid")
            timeout = operation.get("timeout_seconds")
            if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not isfinite(timeout) or timeout <= 0: issues.append(f"operations[{index}].timeout_seconds must be a finite positive number")
            if not _nonempty_string(operation.get("retry_guidance")): issues.append(f"operations[{index}].retry_guidance must be a non-empty string")
            if operation.get("side_effect") == "destructive" and operation.get("idempotency") == "unknown": issues.append(f"operations[{index}] destructive operations cannot have unknown idempotency")

    configuration = _object(root.get("configuration"), "configuration", issues)
    if configuration is not None:
        fields = {"schema", "secret_names"}
        _required(configuration, fields, "configuration", issues); _no_extra(configuration, fields, "configuration", issues)
        config_schema = configuration.get("schema")
        if not isinstance(config_schema, dict): issues.append("configuration.schema must be an object")
        issues.extend(_embedded_schema_issues(config_schema, "configuration.schema"))
        secrets = configuration.get("secret_names")
        if not isinstance(secrets, list) or any(not _nonempty_string(name) or not _SECRET.fullmatch(name) for name in secrets) or len(set(secrets)) != len(secrets): issues.append("configuration.secret_names must be unique uppercase secret names")
        elif isinstance(config_schema, dict):
            normalized_secrets = {re.sub(r"[^a-z0-9]", "", name.lower()) for name in secrets}
            issues.extend(_secret_values_in_schema(config_schema, normalized_secrets))
        if any(isinstance(value, str) and "secret" in key.lower() and key != "secret_names" for key, value in configuration.items()): issues.append("configuration must declare secret names, never secret values")

    safety = _object(root.get("safety"), "safety", issues)
    if safety is not None:
        fields = {"data_classification", "log_redaction", "destructive_opt_in"}
        _required(safety, fields, "safety", issues); _no_extra(safety, fields, "safety", issues)
        if safety.get("data_classification") not in {"public", "internal", "confidential", "restricted"}: issues.append("safety.data_classification is invalid")
        for key in ("log_redaction", "destructive_opt_in"):
            if not isinstance(safety.get(key), bool): issues.append(f"safety.{key} must be a boolean")
        if isinstance(operations, list) and any(isinstance(operation, dict) and operation.get("side_effect") == "destructive" for operation in operations) and safety.get("destructive_opt_in") is not True:
            issues.append("safety.destructive_opt_in must be true when destructive operations are declared")

    health_check = _object(root.get("health_check"), "health_check", issues)
    if health_check is not None:
        _required(health_check, {"operation", "side_effect"}, "health_check", issues); _no_extra(health_check, {"operation", "side_effect"}, "health_check", issues)
        health_operation = health_check.get("operation")
        if health_operation not in operation_names: issues.append("health_check.operation must name a declared operation")
        if health_check.get("side_effect") != "read_only": issues.append("health_check.side_effect must be read_only")
        if isinstance(operations, list):
            matching = [operation for operation in operations if isinstance(operation, dict) and operation.get("name") == health_operation]
            if matching and matching[0].get("side_effect") != "read_only": issues.append("health_check.operation must reference a read_only operation")

    documentation = _object(root.get("documentation"), "documentation", issues)
    if documentation is not None:
        _required(documentation, {"user_guide", "knowledge_base"}, "documentation", issues); _no_extra(documentation, {"user_guide", "knowledge_base"}, "documentation", issues)
        for key in ("user_guide", "knowledge_base"):
            value = documentation.get(key)
            if not _nonempty_string(value) or Path(value).is_absolute() or ".." in Path(value).parts: issues.append(f"documentation.{key} must be a safe relative path")
            elif key == "knowledge_base" and not value.endswith(".json"): issues.append("documentation.knowledge_base must reference a JSON knowledge record")
            elif repository_root is not None:
                resolved_root = repository_root.resolve()
                resolved_path = (repository_root / value).resolve()
                try:
                    resolved_path.relative_to(resolved_root)
                except ValueError:
                    issues.append(f"documentation.{key} must remain within the repository")
                else:
                    if not resolved_path.is_file(): issues.append(f"documentation.{key} must reference an existing file")
    return issues


def load_manifest(path: Path, *, repository_root: Path | None = None) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON number {value}")))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"{path}: cannot read JSON: {error}"]
    issues = validate_manifest(payload, repository_root=repository_root)
    return payload if isinstance(payload, dict) and not issues else None, [f"{path}: {issue}" for issue in issues]


def discover_manifests(root: Path) -> list[Path]:
    adapters = root / "adapters"
    return sorted(adapters.glob("**/adapter.json")) if adapters.is_dir() else []
