"""Clean-room safety primitives for fixed T480 operations; no remote work occurs here."""
from __future__ import annotations
import re
from typing import Any
from tool_repository.contracts import Adapter, AdapterResult, Idempotency, OperationDefinition, SideEffect

_TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@:-]*$")

def validate_target(value: object) -> str:
    if not isinstance(value, str) or not _TARGET.fullmatch(value) or value.startswith("-"):
        raise ValueError("target must be a host alias or user@host without whitespace or options")
    return value

class T480TransportAdapter(Adapter):
    adapter_id = "t480-transport"
    def validate_config(self, config: dict[str, Any]) -> list[str]:
        try: validate_target(config.get("target"))
        except ValueError as error: return [str(error)]
        return []
    def list_operations(self) -> list[OperationDefinition]:
        return [OperationDefinition("validate_target", "Validate a bounded SSH target before a fixed operation is selected.", {"type":"object","required":["target"],"properties":{"target":{"type":"string","pattern":"^[A-Za-z0-9][A-Za-z0-9_.@:-]*$"}},"additionalProperties":False}, {"type":"object","required":["target"],"properties":{"target":{"type":"string"}}}, SideEffect.READ_ONLY, Idempotency.IDEMPOTENT, 1, "No retry is required.")]
    def _invoke_operation(self, operation: OperationDefinition, arguments: dict[str, Any], *, config: dict[str, Any]) -> AdapterResult:
        return AdapterResult(success=True, output={"target": validate_target(arguments["target"])})
    def health_check(self, *, config: dict[str, Any]) -> AdapterResult:
        errors=self.validate_config(config)
        return AdapterResult.failure("invalid_config", "; ".join(errors)) if errors else AdapterResult(success=True, output={"ready": True})
