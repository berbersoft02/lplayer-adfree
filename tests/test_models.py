"""Unit tests for patch engine models."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

from patch_engine.models import (
    PatchRule,
    PatchStrategy,
    Severity,
    ScanFinding,
    PatchResult,
    PatchReport,
)


class TestPatchModels(unittest.TestCase):
    """Tests for PatchRule, ScanFinding, PatchResult, and PatchReport."""

    def test_patch_rule_from_dict(self):
        data = {
            "rule_id": "TEST-001",
            "name": "Test Rule",
            "description": "Test description",
            "category": "test-cat",
            "severity": "critical",
            "target_class_pattern": ".*Test.*",
            "target_method": "doTest",
            "strategy": "stub_return_void",
        }
        rule = PatchRule.from_dict(data)
        self.assertEqual(rule.rule_id, "TEST-001")
        self.assertEqual(rule.severity, Severity.CRITICAL)
        self.assertEqual(rule.strategy, PatchStrategy.STUB_RETURN_VOID)

    def test_patch_report_metrics_and_serialization(self):
        report = PatchReport(
            target_directory=Path("/fake/target"),
            total_files_scanned=5,
            findings=[
                ScanFinding(
                    rule_id="RULE-1",
                    rule_name="Rule 1",
                    category="anti-tamper",
                    severity=Severity.CRITICAL,
                    file_path=Path("A.smali"),
                    line_number=10,
                    matched_text="exit",
                    is_patched=False,
                ),
                ScanFinding(
                    rule_id="RULE-2",
                    rule_name="Rule 2",
                    category="adware",
                    severity=Severity.HIGH,
                    file_path=Path("B.smali"),
                    line_number=20,
                    matched_text="init",
                    is_patched=True,
                ),
            ],
            results=[
                PatchResult(
                    file_path=Path("A.smali"),
                    rule_id="RULE-1",
                    success=True,
                    changes_made=2,
                    message="Neutralized",
                ),
                PatchResult(
                    file_path=Path("C.smali"),
                    rule_id="RULE-3",
                    success=False,
                    changes_made=0,
                    message="Failed",
                ),
            ],
            dry_run=False,
        )

        self.assertEqual(report.total_findings, 2)
        self.assertEqual(report.unpatched_findings, 1)
        self.assertEqual(report.total_changes, 2)

        data = report.to_dict()
        self.assertEqual(data["total_files_scanned"], 5)
        self.assertEqual(data["total_changes"], 2)
        self.assertEqual(len(data["findings"]), 2)
        self.assertEqual(len(data["results"]), 2)

        markdown = report.to_markdown()
        self.assertIn("# Smali Patch Audit Report", markdown)
        self.assertIn("CRITICAL", markdown)
        self.assertIn("RULE-1", markdown)
        self.assertIn("A.smali", markdown)


if __name__ == "__main__":
    unittest.main()
