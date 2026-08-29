"""Read-only, loopback-only readiness checks for approved T480 Ollama models."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Protocol
from urllib.request import urlopen

from tool_repository.contracts import Adapter, AdapterResult, Idempotency, OperationDefinition, SideEffect


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE_PATH = ROOT / "catalogue" / "t480-ollama-model-profiles.json"
_TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_LOOPBACK_TAGS_URL = "http://127.0.0.1:11434/api/tags"


class OllamaInventoryProbe(Protocol):
    """A read-only inventory probe intentionally limited to the local runtime."""

    def inspect_inventory(self) -> list[dict[str, str]]: ...


class LoopbackOllamaInventoryProbe:
    """Read the literal loopback Ollama inventory without submitting prompts."""

    def inspect_inventory(self) -> list[dict[str, str]]:
        with urlopen(_LOOPBACK_TAGS_URL, timeout=10) as response:  # nosec B310: literal loopback URL
            payload = json.load(response)
        models = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(models, list):
            raise ValueError("Ollama inventory does not contain models")
        inventory: list[dict[str, str]] = []
        for item in models:
            if not isinstance(item, dict) or not isinstance(item.get("model"), str) or not isinstance(item.get("digest"), str):
                raise ValueError("Ollama inventory contains an invalid model")
            inventory.append({"model": item["model"], "digest": item["digest"]})
        return inventory


def _approved_models(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    profiles = payload.get("profiles") if isinstance(payload, dict) else None
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("approved profile set is missing")
    approved: dict[str, str] = {}
    for profile in profiles:
        if not isinstance(profile, dict) or not isinstance(profile.get("ollama_model"), str) or not isinstance(profile.get("digest"), str):
            raise ValueError("approved profile is invalid")
        approved[profile["ollama_model"]] = profile["digest"]
    if len(approved) != len(profiles):
        raise ValueError("approved profile models must be unique")
    return approved


def _output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["target", "ready", "endpoint_scope", "checks", "models"],
        "additionalProperties": False,
        "properties": {
            "target": {"type": "string"},
            "ready": {"type": "boolean"},
            "endpoint_scope": {"const": "loopback_only"},
            "checks": {
                "type": "object",
                "additionalProperties": False,
                "required": ["service_reachable", "approved_inventory"],
                "properties": {"service_reachable": {"type": "boolean"}, "approved_inventory": {"type": "boolean"}},
            },
            "models": {
                "type": "array",
                "items": {"type": "object", "additionalProperties": False, "required": ["model", "digest"], "properties": {"model": {"type": "string"}, "digest": {"type": "string", "pattern": "^[a-f0-9]{64}$"}}},
            },
        },
    }


class OllamaReadinessAdapter(Adapter):
    """Compare the local Ollama inventory to the approved digest-pinned set."""

    adapter_id = "ollama-readiness"

    def __init__(self, probe: OllamaInventoryProbe | None = None, *, profile_path: Path = DEFAULT_PROFILE_PATH) -> None:
        self._probe = probe
        self._profile_path = profile_path

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        target = config.get("target")
        return [] if isinstance(target, str) and _TARGET.fullmatch(target) else ["target must be a simple local target label"]

    def list_operations(self) -> list[OperationDefinition]:
        return [OperationDefinition("inspect_inventory", "Read the approved local Ollama inventory through an explicitly supplied loopback probe.", {"type": "object", "additionalProperties": False}, _output_schema(), SideEffect.READ_ONLY, Idempotency.IDEMPOTENT, 10, "Retry after the local Ollama service is restored or the approved profile set is refreshed.")]

    def _invoke_operation(self, operation: OperationDefinition, arguments: dict[str, Any], *, config: dict[str, Any]) -> AdapterResult:
        if self._probe is None:
            return AdapterResult.failure("probe_not_configured", "an explicit loopback-only Ollama inventory probe is required")
        try:
            approved = _approved_models(self._profile_path)
        except (OSError, ValueError, json.JSONDecodeError):
            return AdapterResult.failure("approved_profiles_invalid", "the approved local model profile set is unavailable or invalid")
        try:
            observed = self._probe.inspect_inventory()
        except Exception:
            return AdapterResult.failure("inventory_probe_failed", "the loopback Ollama inventory probe failed", retryable=True)
        if not isinstance(observed, list) or any(not isinstance(item, dict) or set(item) != {"model", "digest"} or not isinstance(item["model"], str) or not isinstance(item["digest"], str) for item in observed):
            return AdapterResult.failure("invalid_probe_result", "the loopback inventory probe returned an invalid model set")
        actual = {item["model"]: item["digest"] for item in observed}
        if len(actual) != len(observed):
            return AdapterResult.failure("invalid_probe_result", "the loopback inventory probe returned duplicate model names")
        matches = actual == approved
        models = [{"model": name, "digest": actual[name]} for name in sorted(actual)]
        return AdapterResult(success=True, output={"target": config["target"], "ready": matches, "endpoint_scope": "loopback_only", "checks": {"service_reachable": True, "approved_inventory": matches}, "models": models})

    def health_check(self, *, config: dict[str, Any]) -> AdapterResult:
        return self.invoke("inspect_inventory", {}, config=config)
