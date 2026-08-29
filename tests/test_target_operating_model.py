from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "docs" / "target_operating_model.md"
MILESTONE = re.compile(r"TR-M[0-9]+[A-Z]?")


class TargetOperatingModelTests(unittest.TestCase):
    def test_capability_status_rows_match_the_registry(self) -> None:
        model = MODEL_PATH.read_text(encoding="utf-8")
        registry = json.loads((ROOT / "milestone_registry.json").read_text(encoding="utf-8"))
        statuses = {item["id"]: item["status"] for item in registry["milestones"]}
        rows = [line for line in model.splitlines() if line.startswith("|") and " | " in line]
        mapped: set[str] = set()
        for row in rows:
            columns = [column.strip() for column in row.strip("|").split("|")]
            if len(columns) != 4 or columns[2] not in {"completed", "in progress", "not started"}:
                continue
            expected = {"completed": "complete", "in progress": "in_progress", "not started": "not_started"}[columns[2]]
            identifiers = MILESTONE.findall(columns[3])
            self.assertTrue(identifiers, row)
            for identifier in identifiers:
                self.assertIn(identifier, statuses, row)
                self.assertEqual(statuses[identifier], expected, row)
                mapped.add(identifier)
        self.assertEqual(mapped, {"TR-M00", "TR-M01A", "TR-M04", "TR-M06", "TR-M09", "TR-M10", "TR-M11", "TR-M12", "TR-M14", "TR-M15", "TR-M16", "TR-M17", "TR-M18", "TR-M19", "TR-M20", "TR-M21", "TR-M22"})


if __name__ == "__main__":
    unittest.main()
