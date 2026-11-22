"""CLI entrypoint for smali patch engine."""

import argparse
import json
import sys
from pathlib import Path

from .engine import PatchEngine


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patch_engine",
        description="Automated Smali Patch Engine for LPlayer Ad-Free Mod & Integrity Bypass",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=None,
        help="Path to custom rules JSON file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan smali directory for targets")
    scan_parser.add_argument("target", type=Path, help="Directory or file containing .smali to scan")
    scan_parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    # Patch command
    patch_parser = subparsers.add_parser("patch", help="Apply smali patches")
    patch_parser.add_argument("target", type=Path, help="Directory or file containing .smali to patch")
    patch_parser.add_argument("--dry-run", action="store_true", help="Simulate patches without modifying files")
    patch_parser.add_argument("--no-backup", action="store_true", help="Do not create .bak backup files")
    patch_parser.add_argument("--report", type=Path, default=None, help="Save report to Markdown or JSON file")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify that no unpatched threats remain")
    verify_parser.add_argument("target", type=Path, help="Directory or file containing .smali to verify")

    return parser


def main(args=None) -> int:
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    engine = PatchEngine(parsed_args.rules)

    if parsed_args.command == "scan":
        report = engine.scan(parsed_args.target)
        if getattr(parsed_args, "json", False):
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(report.to_markdown())
        return 0

    elif parsed_args.command == "patch":
        report = engine.patch(
            target_dir=parsed_args.target,
            dry_run=parsed_args.dry_run,
            backup=not parsed_args.no_backup,
        )

        if parsed_args.report:
            out_path = Path(parsed_args.report)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if out_path.suffix.lower() == ".json":
                out_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
            else:
                out_path.write_text(report.to_markdown(), encoding="utf-8")
            print(f"Report saved to {out_path}")

        print(report.to_markdown())
        return 0

    elif parsed_args.command == "verify":
        passed = engine.verify(parsed_args.target)
        if passed:
            print(f"VERIFICATION SUCCESS: All files in '{parsed_args.target}' are clean and properly patched.")
            return 0
        else:
            print(f"VERIFICATION FAILED: Unpatched vulnerabilities or active threats detected in '{parsed_args.target}'.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
