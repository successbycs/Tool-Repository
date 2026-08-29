from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.milestones import validate_registry


class MilestoneGovernanceTests(unittest.TestCase):
    def test_repository_registry_is_contract_complete(self) -> None:
        self.assertEqual(validate_registry(ROOT), [])

    def test_complete_milestone_requires_real_proof(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            milestone = {
                "id": "TR-M99", "title": "Test", "delivery_type": "foundation_enabling", "status": "complete",
                "capability_unblocked": "test", "dependencies": [], "risk_level": "low",
                "review_requirements": {"required": False, "roles": []}, "write_scope": ["x"],
                "ingestion": {"applies": False, "asset_types": [], "source_records": [], "verification": [], "catalogue_effect": "not_applicable"},
                "required_artifacts": ["x"], "proof_artifact": "runs/proofs/test.json", "verify": ["true"],
                "execution_brief": {"objective": "test", "context": {}, "non_goals": ["none"], "required_outputs": ["x"], "proof_requirements": ["proof"], "verification_commands": ["true"], "stop_conditions": ["stop"]},
            }
            (root / "milestone_registry.json").write_text(json.dumps({"milestones": [milestone]}), encoding="utf-8")
            self.assertTrue(any("required artifact missing" in issue for issue in validate_registry(root)))

    def test_dependency_cycle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = {
                "id": "TR-M97", "title": "First", "delivery_type": "foundation_enabling", "status": "not_started",
                "capability_unblocked": "test", "dependencies": ["TR-M98"], "risk_level": "low",
                "review_requirements": {"required": False, "roles": []}, "write_scope": ["x"], "required_artifacts": ["x"], "proof_artifact": "x", "verify": ["true"],
                "ingestion": {"applies": False, "asset_types": [], "source_records": [], "verification": [], "catalogue_effect": "not_applicable"},
                "execution_brief": {"objective": "test", "context": {}, "non_goals": ["none"], "required_outputs": ["x"], "proof_requirements": ["proof"], "verification_commands": ["true"], "stop_conditions": ["stop"]},
            }
            second = dict(first, id="TR-M98", dependencies=["TR-M97"])
            (root / "milestone_registry.json").write_text(json.dumps({"milestones": [first, second]}), encoding="utf-8")
            self.assertTrue(any("dependency cycle" in issue for issue in validate_registry(root)))

    def test_status_summary_must_match_ordered_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            milestone = {
                "id": "TR-M96", "title": "Summary", "delivery_type": "foundation_enabling", "status": "not_started",
                "capability_unblocked": "test", "dependencies": [], "risk_level": "low",
                "review_requirements": {"required": False, "roles": []}, "write_scope": ["x"], "required_artifacts": ["x"], "proof_artifact": "x", "verify": ["true"],
                "ingestion": {"applies": False, "asset_types": [], "source_records": [], "verification": [], "catalogue_effect": "not_applicable"},
                "execution_brief": {"objective": "test", "context": {}, "non_goals": ["none"], "required_outputs": ["x"], "proof_requirements": ["proof"], "verification_commands": ["true"], "stop_conditions": ["stop"]},
            }
            payload = {"milestone_status_summary": [{"id": "TR-M96", "status": "complete", "title": "Summary"}], "milestones": [milestone]}
            (root / "milestone_registry.json").write_text(json.dumps(payload), encoding="utf-8")
            self.assertTrue(any("milestone_status_summary" in issue for issue in validate_registry(root)))

    def test_ingestion_requires_a_complete_path_when_it_applies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            milestone = {
                "id": "TR-M95", "title": "Ingestion", "delivery_type": "foundation_enabling", "status": "not_started",
                "capability_unblocked": "test", "dependencies": [], "risk_level": "low",
                "review_requirements": {"required": False, "roles": []}, "write_scope": ["x"], "required_artifacts": ["x"], "proof_artifact": "x", "verify": ["true"],
                "ingestion": {"applies": True, "asset_types": ["adapter"], "source_records": [], "verification": [], "catalogue_effect": "publish"},
                "execution_brief": {"objective": "test", "context": {}, "non_goals": ["none"], "required_outputs": ["x"], "proof_requirements": ["proof"], "verification_commands": ["true"], "stop_conditions": ["stop"]},
            }
            (root / "milestone_registry.json").write_text(json.dumps({"milestones": [milestone]}), encoding="utf-8")
            self.assertTrue(any("applicable ingestion requires" in issue for issue in validate_registry(root)))

    def test_complete_ingestion_requires_its_declared_proof_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "records").mkdir()
            (root / "records" / "source.json").write_text("{}", encoding="utf-8")
            (root / "runs" / "proofs").mkdir(parents=True)
            milestone = {
                "id": "TR-M94", "title": "Ingestion proof", "delivery_type": "foundation_enabling", "status": "complete",
                "capability_unblocked": "test", "dependencies": [], "risk_level": "low",
                "review_requirements": {"required": False, "roles": []}, "write_scope": ["x"], "required_artifacts": ["records/source.json"], "proof_artifact": "runs/proofs/test.json", "verify": ["true"],
                "ingestion": {"applies": True, "asset_types": ["adapter"], "source_records": ["records/source.json"], "verification": ["ingestion-check"], "catalogue_effect": "publish"},
                "execution_brief": {"objective": "test", "context": {}, "non_goals": ["none"], "required_outputs": ["x"], "proof_requirements": ["proof"], "verification_commands": ["true"], "stop_conditions": ["stop"]},
            }
            proof = {"milestone_id": "TR-M94", "implementation_revision": "0" * 40, "generated_at": "2026-01-01T00:00:00Z", "environment": {}, "status": "passed", "verification": [{"command": "true", "exit_code": 0, "output": "", "output_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}], "observed_result": "test"}
            (root / "runs" / "proofs" / "test.json").write_text(json.dumps(proof), encoding="utf-8")
            (root / "milestone_registry.json").write_text(json.dumps({"milestones": [milestone]}), encoding="utf-8")
            self.assertTrue(any("missing ingestion verification record" in issue for issue in validate_registry(root)))
