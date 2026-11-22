"""Automated Smali Patch Engine for LPlayer Ad-Free Mod."""

from .models import (
    PatchRule,
    PatchStrategy,
    Severity,
    ScanFinding,
    PatchResult,
    PatchReport,
)
from .scanner import SmaliScanner
from .transformer import SmaliTransformer
from .engine import PatchEngine

__version__ = "1.0.0"

__all__ = [
    "PatchRule",
    "PatchStrategy",
    "Severity",
    "ScanFinding",
    "PatchResult",
    "PatchReport",
    "SmaliScanner",
    "SmaliTransformer",
    "PatchEngine",
]
