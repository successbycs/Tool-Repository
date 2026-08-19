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
                "execution_brief": {"objective": "test", "context": {}, "non_goals": ["none"], "required_outputs": ["x"], "proof_requirements": ["proof"], "verification_commands": ["true"], "stop_conditions": ["stop"]},
            }
            second = dict(first, id="TR-M98", dependencies=["TR-M97"])
            (root / "milestone_registry.json").write_text(json.dumps({"milestones": [first, second]}), encoding="utf-8")
            self.assertTrue(any("dependency cycle" in issue for issue in validate_registry(root)))
