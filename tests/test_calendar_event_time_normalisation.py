from __future__ import annotations

import json
import re
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "calendar-event-time-normalisation" / "expected.json"


class CalendarEventTimeNormalisationTests(unittest.TestCase):
    def test_fixture_preserves_provider_instant_and_uses_explicit_display_source(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1.0.0")
        for case in payload["cases"]:
            local = datetime.fromisoformat(case["event_start"].replace("Z", "+00:00")).astimezone(ZoneInfo(case["timezone"]))
            self.assertEqual(local.strftime("%Y-%m-%d"), case["expected_display_date"], case["id"])
            if case["display_time_source"] == "title_metadata":
                self.assertRegex(case["title_time"], r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$", case["id"])
                self.assertEqual(case["expected_display_time"], case["title_time"], case["id"])
            else:
                self.assertEqual(case["display_time_source"], "event_start", case["id"])
                self.assertEqual(local.strftime("%H:%M"), case["expected_display_time"], case["id"])


if __name__ == "__main__":
    unittest.main()
