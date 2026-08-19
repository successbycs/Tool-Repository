from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.policy_validation import validate_policy_docs


class PolicyValidationTests(unittest.TestCase):
    def test_policy_documents_have_required_metadata_and_index_links(self) -> None:
        self.assertEqual(validate_policy_docs(ROOT), [])

    def test_review_triad_instruction_and_template_exist(self) -> None:
        self.assertTrue((ROOT / "AGENTS.md").exists())
        self.assertTrue((ROOT / "docs" / "milestone_review_triad.md").exists())
