"""Read-only T480 lab readiness adapter with an injected fixed-operation probe.

The adapter deliberately owns no SSH, shell, Docker, or credential behaviour.
A consuming application must supply a narrowly scoped probe implementation.
Default construction cannot contact a host.
"""

from __future__ import annotations

import re
from typing import Any, Protocol

from tool_repository.contracts import Adapter, AdapterResult, Idempotency, OperationDefinition, SideEffect

_TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@:-]*$")
_CHECK_NAMES = ("wsl", "docker", "storage", "ollama", "postgres", "n8n")


class LabRuntimeProbe(Protocol):
    """A fixed, read-only inspection of the named T480 lab target."""

    def inspect_runtime(self, target: str) -> dict[str, bool]: ...


def _valid_target(value: object) -> bool:
    return isinstance(value, str) and bool(_TARGET.fullmatch(value)) and not value.startswith("-")


def _runtime_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["target", "ready", "checks"],
        "properties": {
            "target": {"type": "string"},
            "ready": {"type": "boolean"},
            "checks": {
                "type": "object",
                "required": list(_CHECK_NAMES),
                "additionalProperties": False,
                "properties": {name: {"type": "boolean"} for name in _CHECK_NAMES},
            },
        },
        "additionalProperties": False,
    }


class T480LabAdapter(Adapter):
    """Expose one bounded readiness operation without choosing a transport."""

    adapter_id = "t480-lab"

    def __init__(self, probe: LabRuntimeProbe | None = None) -> None:
        self._probe = probe

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        return [] if _valid_target(config.get("target")) else ["target must be a host alias or user@host without whitespace or options"]

    def list_operations(self) -> list[OperationDefinition]:
        return [
            OperationDefinition(
                "inspect_runtime",
                "Read fixed T480 lab readiness checks through an injected probe.",
                {"type": "object", "additionalProperties": False},
                _runtime_output_schema(),
                SideEffect.READ_ONLY,
                Idempotency.IDEMPOTENT,
                10,
                "Retry after the consuming application restores its fixed transport.",
            )
        ]

    def _invoke_operation(self, operation: OperationDefinition, arguments: dict[str, Any], *, config: dict[str, Any]) -> AdapterResult:
        if self._probe is None:
            return AdapterResult.failure("transport_not_configured", "a fixed read-only lab probe must be supplied by the consuming application")
        try:
            reported = self._probe.inspect_runtime(config["target"])
        except Exception:
            return AdapterResult.failure("transport_probe_failed", "the fixed lab probe did not return a readiness result", retryable=True)
        if not isinstance(reported, dict) or set(reported) != set(_CHECK_NAMES) or any(not isinstance(reported[name], bool) for name in _CHECK_NAMES):
            return AdapterResult.failure("invalid_probe_result", "the fixed lab probe returned an invalid readiness result")
        checks = {name: reported[name] for name in _CHECK_NAMES}
        return AdapterResult(success=True, output={"target": config["target"], "ready": all(checks.values()), "checks": checks})

    def health_check(self, *, config: dict[str, Any]) -> AdapterResult:
        return self.invoke("inspect_runtime", {}, config=config)
