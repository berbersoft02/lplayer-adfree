"""Smali pattern scanner and AST-like parser."""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple, Iterator
import json

from .models import PatchRule, ScanFinding, Severity, PatchStrategy


CLASS_DEF_REGEX = re.compile(r"^\.class\s+.*?(L[a-zA-Z0-9_/$]+;)")
METHOD_DEF_REGEX = re.compile(
    r"^\.method\s+(?P<flags>.*?)\s+(?P<name>[a-zA-Z0-9_$<>]+)\((?P<params>.*?)\)(?P<return>[a-zA-Z0-9_/$\[;]+)"
)
END_METHOD_REGEX = re.compile(r"^\.end\s+method")
INVOKE_REGEX = re.compile(r"^\s*invoke-(?:virtual|static|direct|super|interface)(?:/range)?\s+\{[^\}]*\},\s+(?P<target>.*)")


class SmaliScanner:
    """Scans Smali files for signature patterns and security/ad vulnerabilities."""

    def __init__(self, rules: Optional[List[PatchRule]] = None):
        if rules is None:
            rules_path = Path(__file__).parent / "rules.json"
            if rules_path.exists():
                with open(rules_path, "r", encoding="utf-8") as f:
                    raw_rules = json.load(f)
                    self.rules = [PatchRule.from_dict(r) for r in raw_rules]
            else:
                self.rules = []
        else:
            self.rules = rules

    def find_smali_files(self, target_dir: Path) -> List[Path]:
        """Finds all .smali files recursively under target_dir."""
        target_path = Path(target_dir)
        if not target_path.exists():
            return []
        if target_path.is_file():
            return [target_path] if target_path.suffix == ".smali" else []
        return sorted(list(target_path.rglob("*.smali")))

    def parse_class_name(self, content: str) -> Optional[str]:
        """Extracts class descriptor from smali content."""
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith(".class"):
                m = CLASS_DEF_REGEX.search(line_str)
                if m:
                    return m.group(1)
        return None

    def scan_file(self, file_path: Path) -> List[ScanFinding]:
        """Scans a single smali file against all configured rules."""
        findings: List[ScanFinding] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return findings

        class_desc = self.parse_class_name(content) or ""
        lines = content.splitlines()

        current_method = None
        method_lines: List[str] = []
        method_start_idx = 0

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Method header tracking
            m_def = METHOD_DEF_REGEX.match(stripped)
            if m_def:
                current_method = m_def.group("name")
                method_start_idx = idx
                method_lines = [stripped]
                continue

            if current_method:
                method_lines.append(stripped)
                if END_METHOD_REGEX.match(stripped):
                    # Finished method block
                    method_content = "\n".join(method_lines)
                    self._check_method_rules(
                        file_path=file_path,
                        class_desc=class_desc,
                        method_name=current_method,
                        method_start_idx=method_start_idx,
                        method_content=method_content,
                        findings=findings,
                    )
                    current_method = None
                    method_lines = []

            # Check line-level patterns (e.g. exit calls, signatures)
            self._check_line_rules(
                file_path=file_path,
                class_desc=class_desc,
                line_number=idx,
                line_str=stripped,
                findings=findings,
            )

        return findings

    def _check_method_rules(
        self,
        file_path: Path,
        class_desc: str,
        method_name: str,
        method_start_idx: int,
        method_content: str,
        findings: List[ScanFinding],
    ) -> None:
        """Checks method-level rules."""
        for rule in self.rules:
            if not rule.target_method:
                continue

            # Check class match
            if not re.search(rule.target_class_pattern, class_desc, re.IGNORECASE) and not re.search(rule.target_class_pattern, file_path.name, re.IGNORECASE):
                continue

            # Check method match
            if not re.search(f"^(?:{rule.target_method})$", method_name):
                continue

            # Check if already patched
            is_patched = self._is_method_already_patched(method_content, rule.strategy)

            findings.append(
                ScanFinding(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    category=rule.category,
                    severity=rule.severity,
                    file_path=file_path,
                    line_number=method_start_idx,
                    matched_text=f"Method: {method_name}",
                    is_patched=is_patched,
                )
            )

    def _check_line_rules(
        self,
        file_path: Path,
        class_desc: str,
        line_number: int,
        line_str: str,
        findings: List[ScanFinding],
    ) -> None:
        """Checks single-line signature rules like System.exit or Process.killProcess."""
        for rule in self.rules:
            if not rule.target_signature:
                continue

            # Check class pattern
            if rule.target_class_pattern != ".*" and not re.search(rule.target_class_pattern, class_desc):
                continue

            # Check signature match
            if re.search(rule.target_signature, line_str):
                is_patched = line_str.startswith("# [PATCHED]") or line_str.startswith("#")
                findings.append(
                    ScanFinding(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        category=rule.category,
                        severity=rule.severity,
                        file_path=file_path,
                        line_number=line_number,
                        matched_text=line_str,
                        is_patched=is_patched,
                    )
                )

    def _is_method_already_patched(self, method_content: str, strategy: PatchStrategy) -> bool:
        """Determines if method already exhibits patched bytecode."""
        lines = [l.strip() for l in method_content.splitlines() if l.strip() and not l.strip().startswith("#")]
        # Filter headers and annotations
        body = [
            l for l in lines
            if not l.startswith(".method")
            and not l.startswith(".end")
            and not l.startswith(".annotation")
            and not l.startswith(".end annotation")
        ]

        if strategy == PatchStrategy.STUB_RETURN_VOID:
            # Check for: .locals 0 \n return-void
            return any(l == "return-void" for l in body) and len(body) <= 3
        elif strategy == PatchStrategy.STUB_RETURN_BOOL_TRUE:
            # Check for: const/4 vx, 0x1 \n return vx
            has_const = any("0x1" in l and ("const/4" in l or "const" in l) for l in body)
            has_return = any(l.startswith("return") and l != "return-void" for l in body)
            return has_const and has_return and len(body) <= 4
        elif strategy == PatchStrategy.STUB_RETURN_BOOL_FALSE:
            has_const = any("0x0" in l and ("const/4" in l or "const" in l) for l in body)
            has_return = any(l.startswith("return") and l != "return-void" for l in body)
            return has_const and has_return and len(body) <= 4

        return False

    def scan_directory(self, target_dir: Path) -> Tuple[int, List[ScanFinding]]:
        """Scans all smali files in target directory and aggregates findings."""
        files = self.find_smali_files(target_dir)
        all_findings: List[ScanFinding] = []
        for f in files:
            all_findings.extend(self.scan_file(f))
        return len(files), all_findings
