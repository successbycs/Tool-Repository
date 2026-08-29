from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.catalogue import build_catalogue, load_catalogue, write_catalogue


def release_index() -> dict[str, object]:
    return json.loads((ROOT / "catalogue" / "release-index.json").read_text(encoding="utf-8"))


class CatalogueApiTests(unittest.TestCase):
    def test_builds_sorted_static_catalogue_from_current_descriptors(self) -> None:
        payload, issues = build_catalogue(ROOT)
        self.assertEqual(issues, [])
        assert payload is not None
        entries = payload["adapters"]
        self.assertEqual([(entry["adapter"]["id"], entry["adapter"]["version"]) for entry in entries], sorted((entry["adapter"]["id"], entry["adapter"]["version"]) for entry in entries))
        self.assertTrue(all(entry["release"]["release_tag"] == "v0.1.0" for entry in entries))

    def test_rejects_untrusted_and_checksum_mismatched_release_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "release-index.json"
            index = release_index()
            index["releases"][0]["publisher"] = "untrusted"  # type: ignore[index]
            path.write_text(json.dumps(index), encoding="utf-8")
            _, issues = build_catalogue(ROOT, release_index_path=path)
            self.assertTrue(any("publisher is not trusted" in issue for issue in issues))

            index = release_index()
            index["releases"][0]["manifest_sha256"] = "0" * 64  # type: ignore[index]
            path.write_text(json.dumps(index), encoding="utf-8")
            _, issues = build_catalogue(ROOT, release_index_path=path)
            self.assertTrue(any("release checksum mismatch" in issue for issue in issues))

    def test_rejects_malformed_release_index_and_validates_generated_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            malformed = root / "release-index.json"
            malformed.write_text(json.dumps({"schema_version": "1.0.0"}), encoding="utf-8")
            _, issues = build_catalogue(ROOT, release_index_path=malformed)
            self.assertTrue(any("must contain only" in issue for issue in issues))

            output = root / "adapters.json"
            self.assertEqual(write_catalogue(output, ROOT), [])
            payload, issues = load_catalogue(output)
            self.assertIsNotNone(payload)
            self.assertEqual(issues, [])

    def test_cli_builds_without_importing_adapter_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "adapters.json"
            environment = {"PYTHONPATH": str(ROOT / "src")}
            result = subprocess.run([sys.executable, "-m", "tool_repository", "catalogue", "build", "--output", str(output)], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(output.is_file())
