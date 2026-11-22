"""Unit tests for SmaliScanner."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

from patch_engine.scanner import SmaliScanner
from patch_engine.models import Severity


class TestSmaliScanner(unittest.TestCase):
    """Tests for scanner pattern recognition and classification."""

    def setUp(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.scanner = SmaliScanner()

    def test_find_smali_files(self):
        files = self.scanner.find_smali_files(self.fixtures_dir)
        self.assertGreaterEqual(len(files), 4)
        for f in files:
            self.assertEqual(f.suffix, ".smali")

    def test_scan_pairip_verification(self):
        pairip_file = self.fixtures_dir / "PairIPVerification.smali"
        findings = self.scanner.scan_file(pairip_file)

        rule_ids = [f.rule_id for f in findings]
        self.assertIn("PAIRIP-001", rule_ids)
        self.assertIn("PAIRIP-002", rule_ids)

        exit_finding = next(f for f in findings if f.rule_id == "PAIRIP-002")
        self.assertIn("System;->exit", exit_finding.matched_text)
        self.assertEqual(exit_finding.severity, Severity.CRITICAL)
        self.assertFalse(exit_finding.is_patched)

    def test_scan_mobile_ads_initializer(self):
        gma_file = self.fixtures_dir / "MobileAdsInitializer.smali"
        findings = self.scanner.scan_file(gma_file)

        rule_ids = [f.rule_id for f in findings]
        self.assertIn("GMA-001", rule_ids)

    def test_scan_pangle_initializer(self):
        pangle_file = self.fixtures_dir / "PangleInitializer.smali"
        findings = self.scanner.scan_file(pangle_file)

        rule_ids = [f.rule_id for f in findings]
        self.assertIn("PANGLE-001", rule_ids)

    def test_scan_process_terminator(self):
        term_file = self.fixtures_dir / "ProcessTerminator.smali"
        findings = self.scanner.scan_file(term_file)

        rule_ids = [f.rule_id for f in findings]
        self.assertIn("PAIRIP-002", rule_ids)


if __name__ == "__main__":
    unittest.main()
