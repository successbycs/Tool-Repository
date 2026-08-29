"""Read-only MP4 transcription readiness adapter for a fixed T480 target.

It does not upload media, start jobs, fetch a model, or run arbitrary commands.
Those actions remain application-owned and require a separate future admission.
"""

from __future__ import annotations

import re
from typing import Any, Protocol

from tool_repository.contracts import Adapter, AdapterResult, Idempotency, OperationDefinition, SideEffect

_TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@:-]*$")
_PREFLIGHT_CHECKS = ("inbox_ready", "output_ready", "worker_image_ready")
_RUNTIME_CHECKS = ("worker_running", "model_cache_ready")


class TranscriptionRuntimeProbe(Protocol):
    """A fixed, read-only inspection of the target transcription deployment."""

    def transcription_preflight(self, target: str) -> dict[str, bool]: ...

    def transcription_runtime_status(self, target: str) -> dict[str, bool | int]: ...


def _valid_target(value: object) -> bool:
    return isinstance(value, str) and bool(_TARGET.fullmatch(value)) and not value.startswith("-")


def _preflight_schema() -> dict[str, Any]:
    return {"type": "object", "required": ["target", *_PREFLIGHT_CHECKS], "properties": {"target": {"type": "string"}, **{name: {"type": "boolean"} for name in _PREFLIGHT_CHECKS}}, "additionalProperties": False}


def _runtime_schema() -> dict[str, Any]:
    return {"type": "object", "required": ["target", *_RUNTIME_CHECKS, "active_job_count"], "properties": {"target": {"type": "string"}, **{name: {"type": "boolean"} for name in _RUNTIME_CHECKS}, "active_job_count": {"type": "integer", "minimum": 0}}, "additionalProperties": False}


class Mp4TranscriptionT480Adapter(Adapter):
    """Expose only fixed, read-only transcription deployment diagnostics."""

    adapter_id = "mp4-transcription-t480"

    def __init__(self, probe: TranscriptionRuntimeProbe | None = None) -> None:
        self._probe = probe

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        return [] if _valid_target(config.get("target")) else ["target must be a host alias or user@host without whitespace or options"]

    def list_operations(self) -> list[OperationDefinition]:
        return [
            OperationDefinition("transcription_preflight", "Read fixed inbox, output, and worker-image readiness checks.", {"type": "object", "additionalProperties": False}, _preflight_schema(), SideEffect.READ_ONLY, Idempotency.IDEMPOTENT, 10, "Retry after the consuming application restores the fixed transport or deployment."),
            OperationDefinition("transcription_runtime_status", "Read fixed transcription worker and local-model readiness checks.", {"type": "object", "additionalProperties": False}, _runtime_schema(), SideEffect.READ_ONLY, Idempotency.IDEMPOTENT, 10, "Retry after the consuming application restores the fixed transport or deployment."),
        ]

    def _invoke_operation(self, operation: OperationDefinition, arguments: dict[str, Any], *, config: dict[str, Any]) -> AdapterResult:
        if self._probe is None:
            return AdapterResult.failure("transport_not_configured", "a fixed read-only transcription probe must be supplied by the consuming application")
        try:
            if operation.name == "transcription_preflight":
                reported = self._probe.transcription_preflight(config["target"])
                if not isinstance(reported, dict) or set(reported) != set(_PREFLIGHT_CHECKS) or any(not isinstance(reported[name], bool) for name in _PREFLIGHT_CHECKS):
                    return AdapterResult.failure("invalid_probe_result", "the fixed transcription probe returned an invalid preflight result")
                return AdapterResult(success=True, output={"target": config["target"], **{name: reported[name] for name in _PREFLIGHT_CHECKS}})
            reported = self._probe.transcription_runtime_status(config["target"])
        except Exception:
            return AdapterResult.failure("transport_probe_failed", "the fixed transcription probe did not return a readiness result", retryable=True)
        if not isinstance(reported, dict) or set(reported) != {*_RUNTIME_CHECKS, "active_job_count"} or any(not isinstance(reported[name], bool) for name in _RUNTIME_CHECKS) or isinstance(reported["active_job_count"], bool) or not isinstance(reported["active_job_count"], int) or reported["active_job_count"] < 0:
            return AdapterResult.failure("invalid_probe_result", "the fixed transcription probe returned an invalid runtime result")
        return AdapterResult(success=True, output={"target": config["target"], **{name: reported[name] for name in _RUNTIME_CHECKS}, "active_job_count": reported["active_job_count"]})

    def health_check(self, *, config: dict[str, Any]) -> AdapterResult:
        return self.invoke("transcription_preflight", {}, config=config)
