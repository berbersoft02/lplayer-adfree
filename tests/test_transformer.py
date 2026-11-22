"""Unit tests for SmaliTransformer."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

from patch_engine.scanner import SmaliScanner
from patch_engine.transformer import SmaliTransformer
from patch_engine.models import PatchStrategy


class TestSmaliTransformer(unittest.TestCase):
    """Tests for Smali bytecode transformations and diff generation."""

    def setUp(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.scanner = SmaliScanner()
        self.transformer = SmaliTransformer(self.scanner.rules)

    def test_stub_gma_initialize_method(self):
        file_path = self.fixtures_dir / "MobileAdsInitializer.smali"
        content = file_path.read_text(encoding="utf-8")

        new_content, results = self.transformer.transform_content(content, file_path)

        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].rule_id, "GMA-001")
        self.assertIn("return-void", new_content)
        self.assertNotIn("invoke-static {p0, v0}, Lcom/google/android/gms/ads/MobileAds;->initialize", new_content)

        # Idempotency check: running again shouldn't produce additional modifications
        second_content, second_results = self.transformer.transform_content(new_content, file_path)
        self.assertEqual(len(second_results), 0)
        self.assertEqual(new_content, second_content)

    def test_neutralize_exit_calls(self):
        file_path = self.fixtures_dir / "ProcessTerminator.smali"
        content = file_path.read_text(encoding="utf-8")

        new_content, results = self.transformer.transform_content(content, file_path)

        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].rule_id, "PAIRIP-002")
        self.assertIn("# [PATCHED: neutralized] invoke-static {v0}, Landroid/os/Process;->killProcess(I)V", new_content)
        uncommented_lines = [l.strip() for l in new_content.splitlines() if not l.strip().startswith("#")]
        self.assertNotIn("invoke-static {v0}, Landroid/os/Process;->killProcess(I)V", uncommented_lines)

    def test_stub_pairip_integrity_check(self):
        file_path = self.fixtures_dir / "PairIPVerification.smali"
        content = file_path.read_text(encoding="utf-8")

        new_content, results = self.transformer.transform_content(content, file_path)

        # Should match PAIRIP-001 (stub return bool true) and/or PAIRIP-002 (exit call)
        self.assertTrue(any(r.rule_id == "PAIRIP-001" for r in results))
        self.assertIn("const/4 v0, 0x1", new_content)
        self.assertIn("return v0", new_content)


if __name__ == "__main__":
    unittest.main()
