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


def retarget_manifest(project, **overrides):
    """Rewrite the scaffolded manifest.json with the given key overrides."""
    path = os.path.join(project, "manifest.json")
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest.update(overrides)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)


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
            # empty name is rejected by the name check before touching the filesystem
            self.assertNotEqual(run_cli("new", "", "--dir", tmp).returncode, 0)

    def test_names_with_leading_trailing_hyphens_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("-bad", "bad-", "-", "--", "-a-"):
                result = run_cli("new", "--dir", tmp, "--", bad)
                self.assertNotEqual(result.returncode, 0, bad)
                self.assertIn("hyphen", result.stderr.lower(), bad)
                self.assertFalse(os.path.exists(os.path.join(tmp, bad)), bad)

    def test_single_char_and_digit_names_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            for good in ("a", "9lives", "a-b-2"):
                project = scaffold(good, tmp)
                self.assertTrue(os.path.isfile(os.path.join(project, "manifest.json")))

    def test_dir_must_be_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            not_a_dir = os.path.join(tmp, "notadir")
            with open(not_a_dir, "w", encoding="utf-8") as fh:
                fh.write("i am a file")
            result = run_cli("new", "demo-agent", "--dir", not_a_dir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a directory", result.stderr.lower())
            self.assertNotIn("Traceback", result.stderr)

    def test_target_existing_as_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = os.path.join(tmp, "demo-agent")
            with open(blocker, "w", encoding="utf-8") as fh:
                fh.write("do not touch")
            result = run_cli("new", "demo-agent", "--dir", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a directory", result.stderr.lower())
            self.assertNotIn("Traceback", result.stderr)
            with open(blocker, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "do not touch")

    def test_creates_missing_parent_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "sub", "deep")
            self.assertFalse(os.path.exists(nested))
            result = run_cli("new", "demo-agent", "--dir", nested)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                os.path.isfile(os.path.join(nested, "demo-agent", "agent.py"))
            )

    def test_tilde_in_dir_is_expanded(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = os.path.join(tmp, "fakehome")
            os.makedirs(home)
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = home
            try:
                result = run_cli("new", "demo-agent", "--dir", "~/projects")
            finally:
                if old_home is None:
                    del os.environ["HOME"]
                else:
                    os.environ["HOME"] = old_home
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                os.path.isfile(os.path.join(home, "projects", "demo-agent", "agent.py"))
            )

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

    def test_rejects_nonstring_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            retarget_manifest(project, entrypoint=42)
            result = run_cli("validate", project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("entrypoint", result.stdout.lower())

    def test_rejects_nonstring_required_scalar(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            retarget_manifest(project, version=42)
            result = run_cli("validate", project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("version", result.stdout.lower())

    def test_rejects_skills_not_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            retarget_manifest(project, skills="agent-foundry")
            result = run_cli("validate", project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("skills", result.stdout.lower())

    def test_rejects_skills_nonstring_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            retarget_manifest(project, skills=["agent-foundry", 42])
            result = run_cli("validate", project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("skills", result.stdout.lower())

    def test_rejects_absolute_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            retarget_manifest(project, entrypoint="/etc/hostname")
            result = run_cli("validate", project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("relative", result.stdout.lower())

    def test_rejects_entrypoint_escaping_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside = os.path.join(tmp, "outside_entry.py")
            with open(outside, "w", encoding="utf-8") as fh:
                fh.write("# outside the project\n")
            project = scaffold("demo-agent", tmp)
            retarget_manifest(project, entrypoint="../outside_entry.py")
            result = run_cli("validate", project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("relative", result.stdout.lower())

    def test_accepts_bom_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            path = os.path.join(project, "manifest.json")
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            with open(path, "w", encoding="utf-8-sig") as fh:
                fh.write(content)
            result = run_cli("validate", project)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_scaffolded_agent_handles_bom_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = scaffold("demo-agent", tmp)
            path = os.path.join(project, "manifest.json")
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            with open(path, "w", encoding="utf-8-sig") as fh:
                fh.write(content)
            result = subprocess.run(
                [sys.executable, os.path.join(project, "agent.py"), "--task", "hello"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("demo-agent", result.stdout)


class TestCliMisc(unittest.TestCase):
    def test_version_flag(self):
        result = run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("agent-foundry 0.1.0", result.stdout)

    def test_help_shows_examples(self):
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Examples", result.stdout)
        self.assertIn("new my-agent", result.stdout)
        self.assertIn("validate", result.stdout)


if __name__ == "__main__":
    unittest.main()
