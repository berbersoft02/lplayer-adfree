"""Smali patch engine orchestrator."""

import json
import shutil
from pathlib import Path
from typing import List, Optional

from .models import PatchRule, PatchReport, PatchResult, ScanFinding
from .scanner import SmaliScanner
from .transformer import SmaliTransformer


class PatchEngine:
    """Coordinates scanning, rule matching, bytecode transformations, and reporting."""

    def __init__(self, rules_file: Optional[Path] = None):
        if rules_file and Path(rules_file).exists():
            with open(rules_file, "r", encoding="utf-8") as f:
                raw_rules = json.load(f)
                self.rules = [PatchRule.from_dict(r) for r in raw_rules]
        else:
            default_path = Path(__file__).parent / "rules.json"
            if default_path.exists():
                with open(default_path, "r", encoding="utf-8") as f:
                    raw_rules = json.load(f)
                    self.rules = [PatchRule.from_dict(r) for r in raw_rules]
            else:
                self.rules = []

        self.scanner = SmaliScanner(self.rules)
        self.transformer = SmaliTransformer(self.rules)

    def scan(self, target_dir: Path) -> PatchReport:
        """Performs a read-only scan of smali files in target_dir."""
        target_path = Path(target_dir)
        total_files, findings = self.scanner.scan_directory(target_path)
        return PatchReport(
            target_directory=target_path,
            total_files_scanned=total_files,
            findings=findings,
            results=[],
            dry_run=True,
        )

    def patch(
        self,
        target_dir: Path,
        dry_run: bool = False,
        backup: bool = True,
    ) -> PatchReport:
        """Applies patch rules to all smali files in target_dir."""
        target_path = Path(target_dir)
        files = self.scanner.find_smali_files(target_path)
        all_results: List[PatchResult] = []

        for f in files:
            try:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    orig_content = fh.read()
            except Exception as e:
                all_results.append(
                    PatchResult(
                        file_path=f,
                        rule_id="IO_ERROR",
                        success=False,
                        changes_made=0,
                        message=f"Could not read file: {e}",
                    )
                )
                continue

            new_content, results = self.transformer.transform_content(orig_content, f)
            all_results.extend(results)

            if results and not dry_run:
                if backup:
                    bak_file = f.with_suffix(f.suffix + ".bak")
                    if not bak_file.exists():
                        shutil.copy2(f, bak_file)

                with open(f, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(new_content)

        # After patching or during dry run, re-scan to show post-patch status
        _, post_findings = self.scanner.scan_directory(target_path)

        return PatchReport(
            target_directory=target_path,
            total_files_scanned=len(files),
            findings=post_findings,
            results=all_results,
            dry_run=dry_run,
        )

    def verify(self, target_dir: Path) -> bool:
        """Verifies that all target files in target_dir have zero unpatched findings."""
        target_path = Path(target_dir)
        _, findings = self.scanner.scan_directory(target_path)
        unpatched = [f for f in findings if not f.is_patched]
        return len(unpatched) == 0
