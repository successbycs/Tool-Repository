from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicReadonlyDataProxyPatternTests(unittest.TestCase):
    def test_control_template_and_pattern_keep_the_boundary_explicit(self) -> None:
        template = json.loads((ROOT / "templates/integrations/public-readonly-data-proxy-controls-0.1.0.json").read_text(encoding="utf-8"))
        document = (ROOT / "docs/patterns/public-readonly-data-proxy-controls.md").read_text(encoding="utf-8")
        self.assertEqual(template["id"], "public-readonly-data-proxy-controls")
        self.assertIn("arbitrary outbound URLs", " ".join(template["constraints"]))
        self.assertIn("process-local", " ".join(template["constraints"]))
        for control in ("Allow-list", "CORS", "durable", "rate limiter", "No upstream writes"):
            self.assertIn(control, document)


if __name__ == "__main__":
    unittest.main()
