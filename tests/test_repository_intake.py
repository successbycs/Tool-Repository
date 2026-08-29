from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.repository_intake import load_queue, validate_assessment, validate_queue


class RepositoryIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.queue = json.loads((ROOT / "intake/repository_queue.json").read_text())
        self.assessment = json.loads((ROOT / "intake/assessments/cs-ai-lab-infra.json").read_text())

    def test_current_queue_is_read_only_and_valid(self) -> None:
        self.assertEqual(validate_queue(self.queue, repository_root=ROOT), [])
        payload, issues = load_queue(ROOT / "intake/repository_queue.json", repository_root=ROOT)
        self.assertIsNotNone(payload); self.assertEqual(issues, [])

    def test_queue_requires_exactly_one_assessment(self) -> None:
        queue = copy.deepcopy(self.queue); queue["sources"][0]["status"] = "queued"
        self.assertIn("intake queue must contain exactly one source with status assessing", validate_queue(queue, repository_root=ROOT))

    def test_unresolved_licence_cannot_adopt_or_extract(self) -> None:
        assessment = copy.deepcopy(self.assessment); assessment["candidates"][0]["decision"] = "extract"
        self.assertIn("unresolved licence/provenance requires candidates to be rewrite, defer, reference_only, or reject", validate_assessment(assessment, repository_root=ROOT))

    def test_assessment_rejects_secret_literals(self) -> None:
        assessment = copy.deepcopy(self.assessment); assessment["candidates"][0]["evidence"] = ["API_TOKEN=not-safe"]
        self.assertTrue(any("secret literal" in issue for issue in validate_assessment(assessment, repository_root=ROOT)))
