from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.catalogue import build_catalogue, load_catalogue, write_catalogue


def release_index() -> dict[str, object]:
    return json.loads((ROOT / "catalogue" / "release-index.json").read_text(encoding="utf-8"))


def model_profiles() -> dict[str, object]:
    return json.loads((ROOT / "catalogue" / "t480-ollama-model-profiles.json").read_text(encoding="utf-8"))


class CatalogueApiTests(unittest.TestCase):
    def test_builds_sorted_static_catalogue_from_current_descriptors(self) -> None:
        payload, issues = build_catalogue(ROOT)
        self.assertEqual(issues, [])
        assert payload is not None
        entries = payload["adapters"]
        self.assertEqual([(entry["adapter"]["id"], entry["adapter"]["version"]) for entry in entries], sorted((entry["adapter"]["id"], entry["adapter"]["version"]) for entry in entries))
        self.assertTrue(all(entry["release"]["release_tag"] == "v0.1.0" for entry in entries))

    def test_includes_sorted_local_only_t480_model_profiles(self) -> None:
        payload, issues = build_catalogue(ROOT)
        self.assertEqual(issues, [])
        assert payload is not None
        profiles = payload["model_profiles"]
        self.assertEqual([profile["id"] for profile in profiles], sorted(profile["id"] for profile in profiles))
        self.assertTrue(all(profile["local_only"] for profile in profiles))
        by_id = {profile["id"]: profile for profile in profiles}
        self.assertEqual(by_id["qwen3-4b-q4"]["ollama_model"], "qwen3:4b")
        self.assertEqual(by_id["qwen2.5-coder-7b-q4"]["ollama_model"], "qwen2.5-coder:7b")
        self.assertEqual(set(by_id), {"qwen3-4b-q4", "qwen2.5-coder-7b-q4"})
        self.assertTrue(all(len(profile["digest"]) == 64 for profile in profiles))

    def test_rejects_a_model_profile_without_a_full_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "t480-ollama-model-profiles.json"
            profiles = deepcopy(model_profiles())
            profiles["profiles"][0]["digest"] = "not-a-full-digest"  # type: ignore[index]
            path.write_text(json.dumps(profiles), encoding="utf-8")
            _, issues = build_catalogue(ROOT, model_profiles_path=path)
            self.assertTrue(any("digest must be a full SHA-256" in issue for issue in issues))

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
