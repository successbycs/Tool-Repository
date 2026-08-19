from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jsonschema import Draft202012Validator

from tool_repository.contracts import CONTRACT_VERSION
from tool_repository.manifest import SCHEMA_PATH, load_manifest, validate_manifest


def valid_manifest() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "adapter": {"id": "http-utility", "version": "1.2.3", "contract_version": "1.0.0", "title": "HTTP Utility", "summary": "Makes bounded HTTP requests through a configurable client.", "status": "draft", "owner": "tool-repository", "license": "MIT"},
        "value": {"use_cases": ["Call a documented HTTP endpoint."], "fit_for": ["Solution-neutral integrations."], "not_for": ["Browser automation."], "limitations": ["No retry policy is imposed by this adapter."]},
        "provenance": {"origin": {"source": "local original", "revision": "initial", "license": "MIT", "owner": "tool-repository"}, "changed_from": ""},
        "capabilities": [{"name": "http_request", "description": "Submit one configured HTTP request."}, {"name": "health", "description": "Check local adapter readiness."}],
        "operations": [
            {"name": "request", "summary": "Send one HTTP request.", "capability": "http_request", "input_schema": {"type": "object"}, "output_schema": {"type": "object"}, "side_effect": "mutating", "idempotency": "unknown", "timeout_seconds": 15, "retry_guidance": "Retry only when the caller knows the request is safe."},
            {"name": "health", "summary": "Report adapter readiness.", "capability": "health", "input_schema": {"type": "object"}, "output_schema": {"type": "object"}, "side_effect": "read_only", "idempotency": "idempotent", "timeout_seconds": 3, "retry_guidance": "One retry is safe."}
        ],
        "configuration": {"schema": {"type": "object"}, "secret_names": ["API_TOKEN"]},
        "safety": {"data_classification": "internal", "log_redaction": True, "destructive_opt_in": True},
        "health_check": {"operation": "health", "side_effect": "read_only"},
        "documentation": {"user_guide": "docs/http_utility.md", "knowledge_base": "knowledge/http_utility.json"}
    }


class ManifestValidationTests(unittest.TestCase):
    def test_valid_manifest_passes(self) -> None:
        self.assertEqual(validate_manifest(valid_manifest()), [])

    def test_missing_discovery_value_and_provenance_are_rejected(self) -> None:
        manifest = valid_manifest(); del manifest["value"]
        issues = validate_manifest(manifest)
        self.assertIn("manifest missing required fields: value", issues)

    def test_invalid_semver_and_capability_reference_are_rejected(self) -> None:
        manifest = valid_manifest(); manifest["adapter"]["version"] = "latest"  # type: ignore[index]
        manifest["operations"][0]["capability"] = "unknown"  # type: ignore[index]
        issues = validate_manifest(manifest)
        self.assertIn("adapter.version must be SemVer", issues)
        self.assertIn("operations[0].capability must name a declared capability", issues)

    def test_published_schema_is_valid_and_enforced(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema["properties"]["adapter"]["properties"]["contract_version"]["const"], CONTRACT_VERSION)
        manifest = valid_manifest(); manifest["adapter"]["title"] = "x"  # type: ignore[index]
        self.assertTrue(any("adapter.title" in issue and "too short" in issue for issue in validate_manifest(manifest)))

    def test_invalid_embedded_schema_and_nonfinite_timeout_are_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["operations"][0]["input_schema"] = {"type": "not-a-json-schema-type"}  # type: ignore[index]
        manifest["operations"][0]["timeout_seconds"] = float("nan")  # type: ignore[index]
        issues = validate_manifest(manifest)
        self.assertTrue(any("input_schema must be a valid Draft 2020-12 JSON Schema" in issue for issue in issues))
        self.assertIn("operations[0].timeout_seconds must be a finite positive number", issues)

    def test_destructive_unknown_idempotency_and_secret_value_are_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["operations"][0]["side_effect"] = "destructive"  # type: ignore[index]
        manifest["configuration"]["secret_value"] = "do-not-store"  # type: ignore[index]
        issues = validate_manifest(manifest)
        self.assertIn("operations[0] destructive operations cannot have unknown idempotency", issues)
        self.assertTrue(any("configuration has unsupported fields" in issue for issue in issues))

    def test_cross_field_safety_and_secret_schema_values_are_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["operations"][0]["side_effect"] = "destructive"  # type: ignore[index]
        manifest["operations"][0]["idempotency"] = "idempotent"  # type: ignore[index]
        manifest["safety"]["destructive_opt_in"] = False  # type: ignore[index]
        manifest["health_check"]["operation"] = "request"  # type: ignore[index]
        manifest["configuration"]["schema"] = {"type": "object", "properties": {"api_token": {"type": "string", "default": "live-secret"}}}  # type: ignore[index]
        issues = validate_manifest(manifest)
        self.assertIn("safety.destructive_opt_in must be true when destructive operations are declared", issues)
        self.assertIn("health_check.operation must reference a read_only operation", issues)
        self.assertIn("configuration.schema.properties.api_token.default must not contain a secret value", issues)

    def test_absolute_and_traversal_documentation_paths_are_rejected(self) -> None:
        manifest = valid_manifest(); manifest["documentation"]["user_guide"] = "../outside.md"  # type: ignore[index]
        self.assertIn("documentation.user_guide must be a safe relative path", validate_manifest(manifest))

    def test_load_manifest_checks_documentation_and_rejects_nonfinite_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir(); (root / "knowledge").mkdir()
            (root / "docs" / "http_utility.md").write_text("guide", encoding="utf-8")
            (root / "knowledge" / "http_utility.json").write_text("{}", encoding="utf-8")
            path = root / "adapter.json"
            path.write_text(json.dumps(valid_manifest()), encoding="utf-8")
            payload, issues = load_manifest(path, repository_root=root)
            self.assertIsNotNone(payload); self.assertEqual(issues, [])
            (root / "docs" / "http_utility.md").unlink()
            payload, issues = load_manifest(path, repository_root=root)
            self.assertIsNone(payload); self.assertTrue(any("documentation.user_guide must reference an existing file" in issue for issue in issues))
            path.write_text(json.dumps(valid_manifest()).replace('"timeout_seconds": 15', '"timeout_seconds": NaN'), encoding="utf-8")
            payload, issues = load_manifest(path, repository_root=root)
            self.assertIsNone(payload); self.assertTrue(any("non-finite JSON number NaN" in issue for issue in issues))

    def test_cli_validates_explicit_and_discovered_manifests_without_importing_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters" / "http"; adapter_dir.mkdir(parents=True)
            (root / "docs").mkdir(); (root / "knowledge").mkdir()
            (root / "docs" / "http_utility.md").write_text("guide", encoding="utf-8")
            (root / "knowledge" / "http_utility.json").write_text("{}", encoding="utf-8")
            manifest_path = adapter_dir / "adapter.json"
            manifest_path.write_text(json.dumps(valid_manifest()), encoding="utf-8")
            (adapter_dir / "adapter.py").write_text("raise RuntimeError('must not import')", encoding="utf-8")
            env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
            discovered = subprocess.run([sys.executable, "-m", "tool_repository", "validate"], cwd=root, env=env, text=True, capture_output=True, check=False)
            explicit = subprocess.run([sys.executable, "-m", "tool_repository", "validate", str(manifest_path)], cwd=root, env=env, text=True, capture_output=True, check=False)
            self.assertEqual(discovered.returncode, 0, discovered.stderr + discovered.stdout)
            self.assertEqual(explicit.returncode, 0, explicit.stderr + explicit.stdout)
