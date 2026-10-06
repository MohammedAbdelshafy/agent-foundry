"""Tests for agent-foundry. Run from the repo root: python -m unittest discover -s tests"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(ROOT, "agent_foundry.py")

SCAFFOLD_FILES = (
    "manifest.json",
    "SKILL.md",
    "agent.py",
    os.path.join("tests", "test_agent.py"),
    "README.md",
)


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, CLI, *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def scaffold(name, tmpdir, *extra):
    result = run_cli("new", name, "--dir", tmpdir, *extra)
    assert result.returncode == 0, result.stderr
    return os.path.join(tmpdir, name)


class TestNew(unittest.TestCase):
    def test_scaffolds_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            for rel in SCAFFOLD_FILES:
                self.assertTrue(os.path.isfile(os.path.join(project, rel)), rel)

    def test_manifest_is_valid_json_with_required_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            with open(os.path.join(project, "manifest.json"), encoding="utf-8") as fh:
                manifest = json.load(fh)
            for key in ("name", "version", "description", "entrypoint", "skills"):
                self.assertIn(key, manifest)
            self.assertEqual(manifest["name"], "demo-agent")
            self.assertIsInstance(manifest["skills"], list)

    def test_skill_md_references_agent_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            with open(os.path.join(project, "SKILL.md"), encoding="utf-8") as fh:
                skill = fh.read()
            self.assertIn("demo-agent", skill)
            self.assertTrue(skill.startswith("---\n"))

    def test_invalid_names_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("Bad_Name", "UPPER", "with space", "under_score", "name!"):
                result = run_cli("new", bad, "--dir", tmp)
                self.assertNotEqual(result.returncode, 0, bad)
                self.assertFalse(os.path.exists(os.path.join(tmp, bad)), bad)
            # empty name is rejected by argparse before touching the filesystem
            self.assertNotEqual(run_cli("new", "", "--dir", tmp).returncode, 0)

    def test_refuses_overwrite_nonempty_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "demo-agent")
            os.makedirs(project)
            marker = os.path.join(project, "existing.txt")
            with open(marker, "w", encoding="utf-8") as fh:
                fh.write("do not touch")
            result = run_cli("new", "demo-agent", "--dir", tmp)
            self.assertNotEqual(result.returncode, 0)
            with open(marker, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "do not touch")

    def test_force_overwrites_nonempty(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            result = run_cli("new", "demo-agent", "--dir", tmp, "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(os.path.isfile(os.path.join(project, "agent.py")))


class TestScaffoldedAgent(unittest.TestCase):
    def test_hello_via_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            result = subprocess.run(
                [sys.executable, os.path.join(project, "agent.py"), "--task", "hello"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hello", result.stdout.lower())
            self.assertIn("demo-agent", result.stdout)

    def test_scaffolded_tests_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                capture_output=True,
                text=True,
                cwd=project,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


class TestValidate(unittest.TestCase):
    def test_accepts_good_scaffold(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            result = run_cli("validate", project)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("valid", result.stdout.lower())

    def test_rejects_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            os.remove(os.path.join(project, "SKILL.md"))
            self.assertNotEqual(run_cli("validate", project).returncode, 0)

    def test_rejects_broken_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            with open(os.path.join(project, "manifest.json"), "w", encoding="utf-8") as fh:
                fh.write("{not json")
            self.assertNotEqual(run_cli("validate", project).returncode, 0)

    def test_rejects_missing_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            os.remove(os.path.join(project, "agent.py"))
            self.assertNotEqual(run_cli("validate", project).returncode, 0)

    def test_rejects_missing_dir(self):
        self.assertNotEqual(
            run_cli("validate", "/tmp/definitely-not-a-dir-xyz").returncode, 0
        )


if __name__ == "__main__":
    unittest.main()
