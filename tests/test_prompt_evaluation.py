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

from tool_repository.prompt_evaluation import evaluate_fixture, validate_evaluation_fixture
from tool_repository.prompt_library import load_prompt_library


FIXTURE = ROOT / "examples" / "prompt-evaluation-fixture" / "evaluation-set.json"


class PromptEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definitions, issues = load_prompt_library(ROOT / "prompts" / "definitions")
        self.assertEqual(issues, [])
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_detects_evidenced_drift_and_non_regression_correction(self) -> None:
        report, issues = evaluate_fixture(FIXTURE)
        self.assertEqual(issues, [])
        assert report is not None
        self.assertTrue(report["drift"]["detected"])
        self.assertIn("overall_regression", {event["taxonomy"] for event in report["drift"]["events"]})
        self.assertFalse(report["correction"]["auto_promoted"])
        self.assertTrue(report["correction"]["non_regression_passed"])
        self.assertEqual(report["evaluator"]["sample_size"], 3)
        self.assertEqual(report["rubric"]["version"], "1.0.0")

    def test_fixture_requires_calibration_complete_scores_and_known_prompt(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["evaluator"]["calibration"]["status"] = "failed"
        self.assertTrue(any("calibration.status" in issue for issue in validate_evaluation_fixture(payload, self.definitions)))
        payload = copy.deepcopy(self.payload)
        del payload["samples"][0]["candidate_scores"]["risk_disclosure"]
        self.assertIn("samples[0].candidate_scores must contain exactly the rubric dimension IDs", validate_evaluation_fixture(payload, self.definitions))
        payload = copy.deepcopy(self.payload)
        payload["prompt"]["version"] = "9.9.9"
        self.assertIn("evaluation prompt id/version is not in the validated prompt library", validate_evaluation_fixture(payload, self.definitions))
        payload = copy.deepcopy(self.payload)
        payload["limitations"][0] = "API_TOKEN=do-not-store"
        self.assertTrue(any("secret literal" in issue for issue in validate_evaluation_fixture(payload, self.definitions)))

    def test_non_regression_failure_is_visible_and_never_auto_promoted(self) -> None:
        payload = copy.deepcopy(self.payload)
        for sample in payload["samples"]:
            sample["corrected_scores"]["evidence_grounding"] = 0
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "evaluation-set.json"
            fixture.write_text(json.dumps(payload), encoding="utf-8")
            report, issues = evaluate_fixture(fixture)
        self.assertEqual(issues, [])
        assert report is not None
        self.assertFalse(report["correction"]["non_regression_passed"])
        self.assertTrue(report["correction"]["events"])
        self.assertFalse(report["correction"]["auto_promoted"])

    def test_cli_writes_deterministic_static_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report_path = Path(temp) / "report.json"
            environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
            result = subprocess.run([sys.executable, "-m", "tool_repository", "prompts", "evaluate", "--fixture", "examples/prompt-evaluation-fixture", "--output", str(report_path)], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertTrue(report["drift"]["detected"])
        self.assertEqual(report["correction"]["proposal"]["status"], "proposed")


if __name__ == "__main__":
    unittest.main()
