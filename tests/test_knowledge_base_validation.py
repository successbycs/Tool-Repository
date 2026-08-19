from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.knowledge import load_knowledge_base, validate_knowledge_base
from tests.test_manifest_validation import valid_manifest


def valid_knowledge() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "adapter": {"id": "fixture-http", "version": "0.1.0"},
        "records": [
            {"id": "isolated-test", "kind": "validated_usage", "observed_on": "2026-08-17", "context": "Isolated test with fake transport and no credentials.", "outcome": "Observed normalized adapter responses without provider access.", "constraints_or_lessons": "This does not establish production provider compatibility.", "evidence_ref": "evidence.md", "redaction_attestation": "sanitized_repository_evidence", "reviewed_by": "maintainer"},
            {"id": "candidate-use", "kind": "suggested_use", "use_case": "Use a read-only readiness probe before a workflow begins.", "assumptions": ["A safe readiness endpoint exists."], "validation_required": ["Verify the endpoint has no side effects."]}
        ]
    }


class KnowledgeBaseValidationTests(unittest.TestCase):
    def test_valid_knowledge_base_passes_with_local_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "evidence.md").write_text("safe evidence", encoding="utf-8")
            self.assertEqual(validate_knowledge_base(valid_knowledge(), repository_root=root), [])

    def test_suggested_use_cannot_claim_outcome(self) -> None:
        payload = valid_knowledge(); payload["records"][1]["outcome"] = "It works"  # type: ignore[index]
        issues = validate_knowledge_base(payload)
        self.assertTrue(any("records.1" in issue and "not valid under any" in issue for issue in issues))

    def test_invalid_date_duplicate_ids_and_missing_evidence_are_rejected(self) -> None:
        payload = valid_knowledge()
        payload["records"][0]["observed_on"] = "not-a-date"  # type: ignore[index]
        payload["records"][1]["id"] = "isolated-test"  # type: ignore[index]
        with tempfile.TemporaryDirectory() as temp:
            issues = validate_knowledge_base(payload, repository_root=Path(temp))
        self.assertTrue(any("observed_on" in issue for issue in issues))
        self.assertIn("duplicate knowledge record id: isolated-test", issues)
        self.assertIn("records[0].evidence_ref must reference an existing repository-contained file", issues)

    def test_secret_literals_are_rejected(self) -> None:
        payload = valid_knowledge(); payload["records"][0]["context"] = "API_TOKEN=do-not-store"  # type: ignore[index]
        self.assertIn("knowledge.records[0].context appears to contain a secret literal", validate_knowledge_base(payload))
        payload = valid_knowledge(); payload["records"][0]["context"] = "Authorization: Bearer unredactedcredential"  # type: ignore[index]
        self.assertIn("knowledge.records[0].context appears to contain a secret literal", validate_knowledge_base(payload))

    def test_future_observation_requires_root_and_descriptor_binding(self) -> None:
        payload = valid_knowledge(); payload["records"][0]["observed_on"] = "2099-01-01"  # type: ignore[index]
        issues = validate_knowledge_base(payload, adapter_id="another-adapter", adapter_version="9.9.9")
        self.assertIn("knowledge.adapter.id must match the referencing adapter descriptor", issues)
        self.assertIn("knowledge.adapter.version must match the referencing adapter descriptor", issues)
        self.assertIn("records[0].evidence_ref requires a repository root for admission validation", issues)
        self.assertIn("records[0].observed_on must not be in the future", issues)

    def test_load_and_cli_validate_safe_fixture(self) -> None:
        fixture = ROOT / "examples" / "knowledge-base-fixture" / "knowledge.json"
        payload, issues = load_knowledge_base(fixture, repository_root=ROOT)
        self.assertIsNotNone(payload); self.assertEqual(issues, [])
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run([sys.executable, "-m", "tool_repository", "validate", "--require-knowledge"], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_rejects_knowledge_for_a_different_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); adapter_dir = root / "adapters" / "example"; adapter_dir.mkdir(parents=True)
            (root / "docs").mkdir(); (root / "knowledge").mkdir(); (root / "evidence.md").write_text("safe", encoding="utf-8")
            (root / "docs" / "http_utility.md").write_text("guide", encoding="utf-8")
            manifest = valid_manifest(); manifest["documentation"]["knowledge_base"] = "knowledge/record.json"  # type: ignore[index]
            (adapter_dir / "adapter.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "knowledge" / "record.json").write_text(json.dumps(valid_knowledge()), encoding="utf-8")
            environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
            result = subprocess.run([sys.executable, "-m", "tool_repository", "validate", "--require-knowledge"], cwd=root, env=environment, text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("knowledge.adapter.id must match", result.stdout)
