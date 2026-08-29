from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "minimal-solution"


def load_consumer():
    spec = importlib.util.spec_from_file_location("minimal_solution_consumer", EXAMPLE / "consume_locked_adapter.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SolutionConsumptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.consumer = load_consumer()
        self.lock_path = EXAMPLE / "tool-repository.lock.json"
        self.catalogue_path = ROOT / "catalogue" / "adapters.json"

    def test_lock_resolves_one_exact_catalogue_entry(self) -> None:
        dependency = self.consumer.resolve_catalogue_entry(self.catalogue_path, self.lock_path)
        self.assertEqual(dependency["adapter_id"], "t480-transport")
        self.assertEqual(dependency["adapter_version"], "0.1.0")
        self.assertEqual(dependency["release_tag"], "v0.1.0")
        self.assertEqual(len(dependency["release_commit"]), 40)

    def test_consumer_invokes_locked_adapter_from_detached_immutable_checkout(self) -> None:
        dependency = self.consumer.locked_adapter(self.lock_path)
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp) / "tool-repository"
            added = subprocess.run(
                ["git", "worktree", "add", "--detach", str(checkout), dependency["release_commit"]],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(added.returncode, 0, added.stdout + added.stderr)
            try:
                result = self.consumer.consume(checkout, self.catalogue_path, self.lock_path, "operator@t480")
            finally:
                removed = subprocess.run(
                    ["git", "worktree", "remove", "--force", str(checkout)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(removed.returncode, 0, removed.stdout + removed.stderr)
            self.assertEqual(result["adapter"], "t480-transport@0.1.0")
            self.assertEqual(result["release_commit"], dependency["release_commit"])
            self.assertEqual(result["result"], {"target": "operator@t480"})

    def test_current_mutable_checkout_and_tampered_catalogue_are_rejected(self) -> None:
        dependency = self.consumer.locked_adapter(self.lock_path)
        with self.assertRaisesRegex(ValueError, "locked release commit"):
            self.consumer.verify_pinned_checkout(ROOT, dependency)
        with tempfile.TemporaryDirectory() as temp:
            tampered = Path(temp) / "adapters.json"
            catalogue = json.loads(self.catalogue_path.read_text(encoding="utf-8"))
            transport = next(entry for entry in catalogue["adapters"] if entry["adapter"]["id"] == "t480-transport")
            transport["release"]["release_commit"] = "0" * 40
            tampered.write_text(json.dumps(catalogue), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "release_commit"):
                self.consumer.resolve_catalogue_entry(tampered, self.lock_path)

    def test_fork_provenance_and_docs_preserve_source_release_without_a_local_catalogue(self) -> None:
        lock = json.loads(self.lock_path.read_text(encoding="utf-8"))["dependencies"][0]
        provenance = json.loads((EXAMPLE / "local-fork-provenance.json").read_text(encoding="utf-8"))
        source = provenance["source"]
        for field in ("adapter_id", "adapter_version", "release_tag", "release_commit", "artifact_uri", "manifest_sha256"):
            self.assertEqual(source[field], lock[field])
        self.assertFalse((EXAMPLE / "catalogue.json").exists())
        contribution_guide = (ROOT / "docs" / "contributing_adapters.md").read_text(encoding="utf-8")
        lifecycle = (ROOT / "docs" / "adapter_lifecycle.md").read_text(encoding="utf-8")
        self.assertIn("Never edit a pinned vendor checkout", contribution_guide)
        self.assertIn("full commit", lifecycle)


if __name__ == "__main__":
    unittest.main()
