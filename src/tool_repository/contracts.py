"""Small, transport-neutral contract for reusable Tool Repository adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from math import isfinite
from typing import Any

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
        try:
            result = self._invoke_operation(operation, arguments, config=config)
        except Exception:
            return AdapterResult.failure("adapter_execution_failed", "adapter operation failed")
        if not isinstance(result, AdapterResult):
            return AdapterResult.failure("invalid_adapter_result", "adapter returned an invalid result")
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
