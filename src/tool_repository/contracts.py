"""Small, transport-neutral contract for reusable Tool Repository adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from math import isfinite
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

CONTRACT_VERSION = "1.0.0"


class SideEffect(StrEnum):
    READ_ONLY = "read_only"
    MUTATING = "mutating"
    DESTRUCTIVE = "destructive"


class Idempotency(StrEnum):
    IDEMPOTENT = "idempotent"
    NON_IDEMPOTENT = "non_idempotent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class OperationDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    side_effect: SideEffect
    idempotency: Idempotency
    timeout_seconds: float | None = None
    retry_guidance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """One unambiguous success or failure result, safe for every consumer."""

    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise ValueError("success must be a boolean")
        if not isinstance(self.output, dict) or not isinstance(self.metadata, dict):
            raise ValueError("output and metadata must be objects")
        if self.success:
            if self.error is not None:
                raise ValueError("successful results must not contain error")
            return
        if self.output:
            raise ValueError("failed results must not contain output")
        if not isinstance(self.error, dict):
            raise ValueError("failed results must contain an error object")
        if not isinstance(self.error.get("code"), str) or not self.error["code"].strip():
            raise ValueError("error.code must be a non-empty string")
        if not isinstance(self.error.get("message"), str) or not self.error["message"].strip():
            raise ValueError("error.message must be a non-empty string")
        if not isinstance(self.error.get("retryable"), bool):
            raise ValueError("error.retryable must be a boolean")

    @classmethod
    def failure(cls, code: str, message: str, *, retryable: bool = False, metadata: dict[str, Any] | None = None) -> "AdapterResult":
        return cls(success=False, error={"code": code, "message": message, "retryable": retryable}, metadata=metadata or {})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Adapter(ABC):
    """The only runtime interface every active adapter must implement."""

    adapter_id: str

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Return configuration errors; an empty list means configuration is usable."""

    @abstractmethod
    def list_operations(self) -> list[OperationDefinition]:
        """Return stable operation definitions without performing external work."""

    @abstractmethod
    def _invoke_operation(self, operation: OperationDefinition, arguments: dict[str, Any], *, config: dict[str, Any]) -> AdapterResult:
        """Perform one already-authorized operation and return a normalized result."""

    def invoke(self, operation_name: str, arguments: dict[str, Any], *, config: dict[str, Any], allow_destructive: bool = False) -> AdapterResult:
        if not isinstance(arguments, dict) or not isinstance(config, dict):
            return AdapterResult.failure("invalid_request", "arguments and config must be objects")
        try:
            declared_operations = self.list_operations()
        except Exception:
            return AdapterResult.failure("operation_discovery_failed", "adapter operation discovery failed", retryable=True)
        if not isinstance(declared_operations, list):
            return AdapterResult.failure("invalid_operation_definition", "list_operations must return a list")
        operations: dict[str, OperationDefinition] = {}
        for candidate in declared_operations:
            operation_issues = _validate_operation_definition(candidate)
            if operation_issues:
                return AdapterResult.failure("invalid_operation_definition", "; ".join(operation_issues))
            if candidate.name in operations:
                return AdapterResult.failure("invalid_operation_definition", f"duplicate operation name: {candidate.name}")
            operations[candidate.name] = candidate
        operation = operations.get(operation_name)
        if operation is None:
            return AdapterResult.failure("operation_not_found", f"operation '{operation_name}' is not declared")
        if operation.side_effect is SideEffect.DESTRUCTIVE and allow_destructive is not True:
            return AdapterResult.failure("destructive_opt_in_required", f"operation '{operation_name}' requires explicit destructive opt-in")
        try:
            config_errors = self.validate_config(config)
        except Exception:
            return AdapterResult.failure("config_validation_failed", "adapter configuration validation failed")
        if not isinstance(config_errors, list) or any(not isinstance(error, str) or not error.strip() for error in config_errors):
            return AdapterResult.failure("invalid_config_validation", "adapter returned invalid configuration errors")
        if config_errors:
            return AdapterResult.failure("invalid_config", "; ".join(config_errors))
        argument_issues = _schema_validation_issues(operation.input_schema, arguments)
        if argument_issues:
            return AdapterResult.failure("invalid_arguments", "arguments do not match the declared input schema")
        try:
            result = self._invoke_operation(operation, arguments, config=config)
        except Exception:
            return AdapterResult.failure("adapter_execution_failed", "adapter operation failed")
        if not isinstance(result, AdapterResult):
            return AdapterResult.failure("invalid_adapter_result", "adapter returned an invalid result")
        if result.success and _schema_validation_issues(operation.output_schema, result.output):
            return AdapterResult.failure("invalid_adapter_result", "adapter output does not match the declared output schema")
        return result

    @abstractmethod
    def health_check(self, *, config: dict[str, Any]) -> AdapterResult:
        """Return a normalized readiness result without changing external state."""


def validate_adapter_contract(adapter: Adapter) -> list[str]:
    """Validate static contract invariants without invoking external operations."""

    issues: list[str] = []
    adapter_id = getattr(adapter, "adapter_id", None)
    if not isinstance(adapter_id, str) or not adapter_id.strip():
        issues.append("adapter_id must be a non-empty string")
    try:
        operations = adapter.list_operations()
    except Exception as error:
        return [*issues, f"list_operations raised {type(error).__name__}"]
    if not isinstance(operations, list):
        return [*issues, "list_operations must return a list"]
    names: set[str] = set()
    for operation in operations:
        operation_issues = _validate_operation_definition(operation)
        if operation_issues:
            issues.extend(operation_issues)
            continue
        if not isinstance(operation.name, str) or not operation.name.strip():
            issues.append("operation name must be non-empty")
        elif operation.name in names:
            issues.append(f"duplicate operation name: {operation.name}")
        names.add(operation.name)
    return issues


def validate_adapter_manifest_conformance(adapter: Adapter, manifest: Any) -> list[str]:
    """Compare an explicitly loaded descriptor with an explicitly loaded adapter.

    Manifest discovery remains static; this check is only for an admission test
    that has deliberately imported the candidate adapter.
    """

    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    issues = validate_adapter_contract(adapter)
    adapter_data = manifest.get("adapter")
    if not isinstance(adapter_data, dict) or adapter_data.get("id") != getattr(adapter, "adapter_id", None):
        issues.append("runtime adapter_id must match manifest adapter.id")
    declared = manifest.get("operations")
    if not isinstance(declared, list):
        return [*issues, "manifest operations must be a list"]
    try:
        runtime_operations = adapter.list_operations()
    except Exception as error:
        return [*issues, f"list_operations raised {type(error).__name__}"]
    if not isinstance(runtime_operations, list):
        return [*issues, "list_operations must return a list"]
    runtime_by_name = {operation.name: operation for operation in runtime_operations if isinstance(operation, OperationDefinition)}
    manifest_by_name = {item.get("name"): item for item in declared if isinstance(item, dict) and isinstance(item.get("name"), str)}
    if set(runtime_by_name) != set(manifest_by_name):
        issues.append("runtime operations must exactly match manifest operations")
    for name in sorted(set(runtime_by_name) & set(manifest_by_name)):
        runtime = runtime_by_name[name]
        descriptor = manifest_by_name[name]
        expected = {
            "input_schema": runtime.input_schema,
            "output_schema": runtime.output_schema,
            "side_effect": runtime.side_effect.value,
            "idempotency": runtime.idempotency.value,
            "timeout_seconds": runtime.timeout_seconds,
            "retry_guidance": runtime.retry_guidance,
        }
        for field, value in expected.items():
            if descriptor.get(field) != value:
                issues.append(f"runtime operation {name}.{field} must match the manifest")
    health = manifest.get("health_check")
    if isinstance(health, dict):
        operation = runtime_by_name.get(health.get("operation"))
        if operation is None or operation.side_effect is not SideEffect.READ_ONLY:
            issues.append("manifest health_check must reference a runtime read_only operation")
    else:
        issues.append("manifest health_check must be an object")
    return issues


def _validate_operation_definition(operation: Any) -> list[str]:
    if not isinstance(operation, OperationDefinition):
        return ["list_operations must return OperationDefinition instances"]
    issues: list[str] = []
    if not isinstance(operation.name, str) or not operation.name.strip():
        issues.append("operation name must be a non-empty string")
    if not isinstance(operation.description, str) or not operation.description.strip():
        issues.append(f"{operation.name}: description must be non-empty")
    if not isinstance(operation.input_schema, dict) or not isinstance(operation.output_schema, dict):
        issues.append(f"{operation.name}: input_schema and output_schema must be objects")
    else:
        for label, schema in (("input_schema", operation.input_schema), ("output_schema", operation.output_schema)):
            try:
                Draft202012Validator.check_schema(schema)
            except SchemaError:
                issues.append(f"{operation.name}: {label} must be a valid Draft 2020-12 JSON Schema")
    if not isinstance(operation.side_effect, SideEffect):
        issues.append(f"{operation.name}: side_effect must be a SideEffect")
    if not isinstance(operation.idempotency, Idempotency):
        issues.append(f"{operation.name}: idempotency must be an Idempotency")
    if operation.timeout_seconds is not None:
        timeout = operation.timeout_seconds
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not isfinite(timeout) or timeout <= 0:
            issues.append(f"{operation.name}: timeout_seconds must be a finite positive number when provided")
    if operation.side_effect is SideEffect.DESTRUCTIVE and operation.idempotency is Idempotency.UNKNOWN:
        issues.append(f"{operation.name}: destructive operations must declare idempotency")
    return issues


def _schema_validation_issues(schema: dict[str, Any], value: dict[str, Any]) -> list[str]:
    """Return schema errors without reflecting caller data into normalized results."""

    try:
        validator = Draft202012Validator(schema)
    except SchemaError:
        return ["invalid schema"]
    return [error.message for error in validator.iter_errors(value)]
