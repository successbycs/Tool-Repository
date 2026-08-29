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

from tool_repository.prompt_library import load_prompt_execution, load_prompt_library, validate_prompt_definition, validate_prompt_execution


def execution(definition_sha256: str, *, prompt_id: str = "repository-asset-assessment", version: str = "1.0.0") -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "execution_id": "exec-0001",
        "occurred_at": "2026-08-29T03:30:00Z",
        "prompt": {"id": prompt_id, "version": version, "definition_sha256": definition_sha256},
        "context": {"kind": "repository_intake", "reference": "intake/assessments/example.json"},
        "runtime": {"provider": "approved-provider", "model": "approved-model", "settings_profile": "safe-v1"},
        "input_capture": {"mode": "redacted_canonical", "canonical_sha256": "a" * 64, "reference": "protected://solution/input/123"},
        "output_capture": {"mode": "protected_reference", "canonical_sha256": "b" * 64, "reference": "protected://solution/output/123"},
        "outcome": {"status": "success", "evidence_sha256": "c" * 64},
        "redaction_attestation": "no_secrets_or_private_content",
    }


class PromptLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definitions, self.issues = load_prompt_library(ROOT / "prompts" / "definitions")
        self.assertEqual(self.issues, [])
        self.definition = self.definitions[("repository-asset-assessment", "1.0.0")]

    def test_checked_in_library_and_cli_validate_without_execution(self) -> None:
        self.assertEqual(
            set(self.definitions),
            {("goal-definition-and-milestone-seed", "1.0.0"), ("repository-asset-assessment", "1.0.0")},
        )
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run([sys.executable, "-m", "tool_repository", "prompts", "validate"], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_redacted_execution_is_auditable_and_binds_definition_bytes(self) -> None:
        payload = execution(self.definition["sha256"])
        self.assertEqual(validate_prompt_execution(payload, self.definitions), [])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "execution.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded, issues = load_prompt_execution(path, self.definitions)
        self.assertIsNotNone(loaded)
        self.assertEqual(issues, [])

    def test_raw_content_secrets_and_hidden_reasoning_are_rejected(self) -> None:
        payload = execution(self.definition["sha256"])
        payload["rendered_prompt"] = "This must never be stored"
        issues = validate_prompt_execution(payload, self.definitions)
        self.assertTrue(any("rendered_prompt" in issue for issue in issues))
        payload = execution(self.definition["sha256"])
        payload["input_capture"]["reference"] = "Authorization: Bearer unredactedcredential"  # type: ignore[index]
        self.assertTrue(any("secret literal" in issue for issue in validate_prompt_execution(payload, self.definitions)))
        payload = execution(self.definition["sha256"])
        payload["chain_of_thought"] = "private reasoning"
        self.assertTrue(any("chain_of_thought" in issue for issue in validate_prompt_execution(payload, self.definitions)))

    def test_unknown_or_tampered_definition_reference_is_rejected(self) -> None:
        payload = execution("0" * 64)
        self.assertIn("execution prompt definition_sha256 does not match the validated definition bytes", validate_prompt_execution(payload, self.definitions))
        payload = execution(self.definition["sha256"], version="9.9.9")
        self.assertIn("execution prompt id/version is not in the validated prompt library", validate_prompt_execution(payload, self.definitions))

    def test_restricted_definition_requires_protected_reference_capture(self) -> None:
        payload = copy.deepcopy(self.definition["payload"])
        payload["data_classification"] = "restricted"
        payload["rendering"]["execution_capture"] = "redacted_canonical"
        self.assertIn("restricted prompt definitions must require protected_reference execution capture", validate_prompt_definition(payload))


if __name__ == "__main__":
    unittest.main()
