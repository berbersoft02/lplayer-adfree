"""Unit tests for patch engine CLI."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout

from patch_engine.cli import main


class TestPatchCLI(unittest.TestCase):
    """Tests for CLI argument processing and exit codes."""

    def setUp(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_cli_"))
        for f in self.fixtures_dir.glob("*.smali"):
            shutil.copy2(f, self.temp_dir / f.name)

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_cli_scan(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["scan", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)
        output = f.getvalue()
        self.assertIn("Smali Patch Audit Report", output)
        self.assertIn("PAIRIP-001", output)

    def test_cli_scan_json(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["scan", str(self.temp_dir), "--json"])
        self.assertEqual(exit_code, 0)
        output = f.getvalue()
        self.assertIn('"total_files_scanned":', output)

    def test_cli_patch_dry_run(self):
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["patch", str(self.temp_dir), "--dry-run"])
        self.assertEqual(exit_code, 0)
        output = f.getvalue()
        self.assertIn("Dry Run", output)

    def test_cli_patch_and_verify(self):
        # Verification fails before patch
        f_pre = io.StringIO()
        with redirect_stdout(f_pre):
            pre_code = main(["verify", str(self.temp_dir)])
        self.assertEqual(pre_code, 1)

        # Patch execution
        report_path = self.temp_dir / "report.md"
        f_patch = io.StringIO()
        with redirect_stdout(f_patch):
            patch_code = main(["patch", str(self.temp_dir), "--report", str(report_path)])
        self.assertEqual(patch_code, 0)
        self.assertTrue(report_path.exists())

        # Verification passes after patch
        f_post = io.StringIO()
        with redirect_stdout(f_post):
            post_code = main(["verify", str(self.temp_dir)])
        self.assertEqual(post_code, 0)
        self.assertIn("VERIFICATION SUCCESS", f_post.getvalue())


if __name__ == "__main__":
    unittest.main()
