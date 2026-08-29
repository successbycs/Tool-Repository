from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.contracts import SideEffect, validate_adapter_contract, validate_adapter_manifest_conformance
from tool_repository.manifest import load_manifest


def load_class(relative_path: str, class_name: str):
    spec = importlib.util.spec_from_file_location(class_name, ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def load_adapter_manifest(adapter_name: str) -> dict[str, object]:
    manifest, issues = load_manifest(ROOT / "adapters" / adapter_name / "adapter.json", repository_root=ROOT)
    assert manifest is not None, issues
    return manifest


class FakeLabProbe:
    def inspect_runtime(self, target: str) -> dict[str, bool]:
        assert target == "operator@t480"
        return {"wsl": True, "docker": True, "storage": True, "ollama": True, "postgres": True, "n8n": False}


class FakeTranscriptionProbe:
    def transcription_preflight(self, target: str) -> dict[str, bool]:
        assert target == "operator@t480"
        return {"inbox_ready": True, "output_ready": True, "worker_image_ready": True}

    def transcription_runtime_status(self, target: str) -> dict[str, bool | int]:
        assert target == "operator@t480"
        return {"worker_running": False, "model_cache_ready": True, "active_job_count": 0}


class FakeOllamaProbe:
    def __init__(self, *, mismatch: bool = False) -> None:
        profiles = json.loads((ROOT / "catalogue" / "t480-ollama-model-profiles.json").read_text(encoding="utf-8"))["profiles"]
        self._inventory = [{"model": profile["ollama_model"], "digest": profile["digest"]} for profile in profiles]
        if mismatch:
            self._inventory[0] = {"model": self._inventory[0]["model"], "digest": "0" * 64}

    def inspect_inventory(self) -> list[dict[str, str]]:
        return self._inventory


class T480AdapterConformanceTests(unittest.TestCase):
    def test_transport_validates_locally_and_matches_its_manifest(self) -> None:
        adapter_type = load_class("adapters/t480-transport/transport.py", "T480TransportAdapter")
        adapter = adapter_type()
        manifest = load_adapter_manifest("t480-transport")
        self.assertEqual(validate_adapter_contract(adapter), [])
        self.assertEqual(validate_adapter_manifest_conformance(adapter, manifest), [])
        self.assertTrue(adapter.invoke("validate_target", {"target": "operator@t480"}, config={"target": "operator@t480"}).success)
        self.assertEqual(adapter.invoke("validate_target", {"target": "-oProxyCommand=x"}, config={"target": "operator@t480"}).error["code"], "invalid_arguments")

    def test_lab_adapter_uses_fake_read_only_probe_and_matches_manifest(self) -> None:
        adapter_type = load_class("adapters/t480-lab/adapter.py", "T480LabAdapter")
        adapter = adapter_type(FakeLabProbe())
        manifest = load_adapter_manifest("t480-lab")
        self.assertEqual(validate_adapter_contract(adapter), [])
        self.assertEqual(validate_adapter_manifest_conformance(adapter, manifest), [])
        self.assertTrue(all(operation.side_effect is SideEffect.READ_ONLY for operation in adapter.list_operations()))
        result = adapter.health_check(config={"target": "operator@t480"})
        self.assertTrue(result.success)
        self.assertEqual(result.output["ready"], False)
        self.assertEqual(result.output["checks"]["n8n"], False)
        self.assertEqual(adapter.invoke("inspect_runtime", {}, config={"target": "-oProxyCommand=x"}).error["code"], "invalid_config")
        self.assertEqual(adapter_type().health_check(config={"target": "operator@t480"}).error["code"], "transport_not_configured")

    def test_transcription_adapter_uses_fake_read_only_probe_and_matches_manifest(self) -> None:
        adapter_type = load_class("adapters/mp4-transcription-t480/adapter.py", "Mp4TranscriptionT480Adapter")
        adapter = adapter_type(FakeTranscriptionProbe())
        manifest = load_adapter_manifest("mp4-transcription-t480")
        self.assertEqual(validate_adapter_contract(adapter), [])
        self.assertEqual(validate_adapter_manifest_conformance(adapter, manifest), [])
        self.assertTrue(all(operation.side_effect is SideEffect.READ_ONLY for operation in adapter.list_operations()))
        preflight = adapter.health_check(config={"target": "operator@t480"})
        runtime = adapter.invoke("transcription_runtime_status", {}, config={"target": "operator@t480"})
        self.assertTrue(preflight.success)
        self.assertTrue(runtime.success)
        self.assertEqual(runtime.output["active_job_count"], 0)
        self.assertEqual(runtime.output["worker_running"], False)
        self.assertEqual(adapter_type().health_check(config={"target": "operator@t480"}).error["code"], "transport_not_configured")

    def test_ollama_readiness_uses_a_fake_loopback_probe_and_rejects_mismatch(self) -> None:
        adapter_type = load_class("adapters/ollama-readiness/adapter.py", "OllamaReadinessAdapter")
        adapter = adapter_type(FakeOllamaProbe())
        manifest = load_adapter_manifest("ollama-readiness")
        self.assertEqual(validate_adapter_contract(adapter), [])
        self.assertEqual(validate_adapter_manifest_conformance(adapter, manifest), [])
        result = adapter.health_check(config={"target": "t480"})
        self.assertTrue(result.success)
        self.assertTrue(result.output["ready"])
        self.assertEqual(result.output["endpoint_scope"], "loopback_only")
        mismatch = adapter_type(FakeOllamaProbe(mismatch=True)).health_check(config={"target": "t480"})
        self.assertTrue(mismatch.success)
        self.assertFalse(mismatch.output["ready"])
        self.assertEqual(adapter_type().health_check(config={"target": "t480"}).error["code"], "probe_not_configured")


if __name__ == "__main__":
    unittest.main()
