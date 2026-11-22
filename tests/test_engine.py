"""Unit tests for PatchEngine orchestrator."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shutil
import tempfile
import unittest

from patch_engine.engine import PatchEngine


class TestPatchEngine(unittest.TestCase):
    """Tests for PatchEngine workflows (scan, patch, verify, dry-run, backup)."""

    def setUp(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_smali_patch_"))
        # Copy fixtures to temp dir
        for f in self.fixtures_dir.glob("*.smali"):
            shutil.copy2(f, self.temp_dir / f.name)

        self.engine = PatchEngine()

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_scan_unpatched_directory(self):
        report = self.engine.scan(self.temp_dir)
        self.assertGreater(report.total_files_scanned, 0)
        self.assertGreater(report.total_findings, 0)
        self.assertGreater(report.unpatched_findings, 0)
        self.assertTrue(report.dry_run)

    def test_dry_run_patch(self):
        report = self.engine.patch(self.temp_dir, dry_run=True, backup=False)
        self.assertTrue(report.dry_run)
        self.assertGreater(len(report.results), 0)

        # Ensure no .bak files were created
        bak_files = list(self.temp_dir.glob("*.bak"))
        self.assertEqual(len(bak_files), 0)

        # Verification should fail because files were not actually modified
        self.assertFalse(self.engine.verify(self.temp_dir))

    def test_live_patch_and_verify(self):
        # Initial verification fails
        self.assertFalse(self.engine.verify(self.temp_dir))

        # Apply live patch with backup
        report = self.engine.patch(self.temp_dir, dry_run=False, backup=True)
        self.assertFalse(report.dry_run)
        self.assertGreater(report.total_changes, 0)

        # Verify backup files created
        bak_files = list(self.temp_dir.glob("*.bak"))
        self.assertGreater(len(bak_files), 0)

        # Verification should now pass
        self.assertTrue(self.engine.verify(self.temp_dir))


if __name__ == "__main__":
    unittest.main()
