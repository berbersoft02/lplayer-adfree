"""Data models for Smali patch engine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


class PatchStrategy(str, Enum):
    """Supported bytecode transformation strategies."""
    STUB_RETURN_VOID = "stub_return_void"
    STUB_RETURN_BOOL_TRUE = "stub_return_bool_true"
    STUB_RETURN_BOOL_FALSE = "stub_return_bool_false"
    NEUTRALIZE_EXIT_CALLS = "neutralize_exit_calls"
    COMMENT_INVOCATION = "comment_invocation"


class Severity(str, Enum):
    """Severity or impact level of detected pattern."""
    CRITICAL = "critical"  # Anti-tamper, forced exit
    HIGH = "high"          # Interstitial / tracking ad SDK
    MEDIUM = "medium"      # Telemetry / background beacon
    LOW = "low"            # Informational / minor tracking


@dataclass
class PatchRule:
    """Represents a declarative rule for identifying and patching Smali code."""
    rule_id: str
    name: str
    description: str
    category: str
    severity: Severity
    target_class_pattern: str
    target_method: Optional[str] = None
    target_signature: Optional[str] = None
    strategy: PatchStrategy = PatchStrategy.STUB_RETURN_VOID
    replacement_instructions: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatchRule":
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "adware"),
            severity=Severity(data.get("severity", "high")),
            target_class_pattern=data["target_class_pattern"],
            target_method=data.get("target_method"),
            target_signature=data.get("target_signature"),
            strategy=PatchStrategy(data.get("strategy", "stub_return_void")),
            replacement_instructions=data.get("replacement_instructions"),
        )


@dataclass
class ScanFinding:
    """Represents a matched pattern or unpatched routine discovered during scanning."""
    rule_id: str
    rule_name: str
    category: str
    severity: Severity
    file_path: Path
    line_number: int
    matched_text: str
    is_patched: bool = False


@dataclass
class PatchResult:
    """Result of applying a patch to a specific file."""
    file_path: Path
    rule_id: str
    success: bool
    changes_made: int
    message: str
    diff: Optional[str] = None


@dataclass
class PatchReport:
    """Comprehensive summary report of a scan or patch operation."""
    target_directory: Path
    total_files_scanned: int = 0
    findings: List[ScanFinding] = field(default_factory=list)
    results: List[PatchResult] = field(default_factory=list)
    dry_run: bool = False

    @property
    def total_changes(self) -> int:
        return sum(r.changes_made for r in self.results if r.success)

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def unpatched_findings(self) -> int:
        return sum(1 for f in self.findings if not f.is_patched)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_directory": str(self.target_directory),
            "dry_run": self.dry_run,
            "total_files_scanned": self.total_files_scanned,
            "total_findings": self.total_findings,
            "unpatched_findings": self.unpatched_findings,
            "total_changes": self.total_changes,
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "rule_name": f.rule_name,
                    "category": f.category,
                    "severity": f.severity.value,
                    "file_path": str(f.file_path),
                    "line_number": f.line_number,
                    "matched_text": f.matched_text,
                    "is_patched": f.is_patched,
                }
                for f in self.findings
            ],
            "results": [
                {
                    "file_path": str(r.file_path),
                    "rule_id": r.rule_id,
                    "success": r.success,
                    "changes_made": r.changes_made,
                    "message": r.message,
                }
                for r in self.results
            ],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Smali Patch Audit Report",
            f"- **Target Directory:** `{self.target_directory}`",
            f"- **Mode:** `{'Dry Run' if self.dry_run else 'Live Execution'}`",
            f"- **Files Scanned:** {self.total_files_scanned}",
            f"- **Findings Detected:** {self.total_findings} ({self.unpatched_findings} unpatched)",
            f"- **Modifications Applied:** {self.total_changes}",
            "",
            "## Summary of Findings",
        ]
        if not self.findings:
            lines.append("No active or unpatched signatures detected.")
        else:
            lines.append("| Severity | Rule ID | Category | File | Line | Status |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for f in self.findings:
                status = "Patched" if f.is_patched else "**Unpatched**"
                rel_path = f.file_path.name
                lines.append(f"| {f.severity.value.upper()} | `{f.rule_id}` | {f.category} | `{rel_path}` | {f.line_number} | {status} |")

        if self.results:
            lines.append("")
            lines.append("## Patch Execution Results")
            lines.append("| Rule ID | File | Success | Modifications | Details |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for r in self.results:
                status_icon = "PASS" if r.success else "FAIL"
                lines.append(f"| `{r.rule_id}` | `{r.file_path.name}` | {status_icon} | {r.changes_made} | {r.message} |")

        return "\n".join(lines)
