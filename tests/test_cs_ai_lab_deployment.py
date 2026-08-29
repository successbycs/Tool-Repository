from __future__ import annotations

import getpass
import json
import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "deploy" / "cs-ai-lab" / "install.sh"
ROLLBACK = ROOT / "deploy" / "cs-ai-lab" / "rollback.sh"
VERIFY = ROOT / "scripts" / "verify_cs_ai_lab_deploy.py"


def run(*command: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def fixture_repository(root: Path) -> Path:
    source = root / "source"
    source.mkdir()
    run("git", "init", "-q", str(source))
    (source / "payload.txt").write_text("first release\n", encoding="utf-8")
    run("git", "-C", str(source), "add", "payload.txt")
    run("git", "-C", str(source), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "first")
    run("git", "-C", str(source), "tag", "v0.1.0")
    return source


class CsAiLabDeploymentTests(unittest.TestCase):
    def test_install_and_rollback_switch_only_versioned_release_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = fixture_repository(root)
            install_root = root / "installed"
            account = getpass.getuser()
            first = run(str(INSTALL), "--source", str(source), "--release", "v0.1.0", "--install-root", str(install_root), "--account", account)
            first_metadata = json.loads(Path(first.stdout.strip()).read_text(encoding="utf-8"))
            first_id = f"{first_metadata['release_tag']}-{first_metadata['commit'][:12]}"
            self.assertTrue((install_root / "current").is_symlink())
            self.assertEqual((install_root / "current" / "payload.txt").read_text(encoding="utf-8"), "first release\n")

            (source / "payload.txt").write_text("second release\n", encoding="utf-8")
            run("git", "-C", str(source), "add", "payload.txt")
            run("git", "-C", str(source), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "second")
            run("git", "-C", str(source), "tag", "v0.1.1")
            run(str(INSTALL), "--source", str(source), "--release", "v0.1.1", "--install-root", str(install_root), "--account", account)
            self.assertEqual((install_root / "current" / "payload.txt").read_text(encoding="utf-8"), "second release\n")
            run(str(ROLLBACK), "--install-root", str(install_root), "--release-id", first_id, "--account", account)
            self.assertEqual((install_root / "current" / "payload.txt").read_text(encoding="utf-8"), "first release\n")

    def test_verifier_checks_identity_and_resolvable_release_without_deploying(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = fixture_repository(Path(temp))
            result = run(sys.executable, str(VERIFY), "--host", platform.node(), "--account", getpass.getuser(), "--release", "v0.1.0", "--source", str(source))
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["release"], "v0.1.0")

    def test_installer_rejects_an_account_other_than_the_current_user(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = fixture_repository(Path(temp))
            result = subprocess.run([str(INSTALL), "--source", str(source), "--release", "v0.1.0", "--install-root", str(Path(temp) / "installed"), "--account", "not-the-current-user"], text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("declared non-root account", result.stderr)
