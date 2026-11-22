"""Smali bytecode transformation engine."""

import difflib
import re
from pathlib import Path
from typing import List, Optional, Tuple

from .models import PatchRule, PatchResult, PatchStrategy
from .scanner import METHOD_DEF_REGEX, END_METHOD_REGEX, CLASS_DEF_REGEX


class SmaliTransformer:
    """Applies bytecode transformations according to patch rules."""

    def __init__(self, rules: List[PatchRule]):
        self.rules = rules

    def transform_content(self, content: str, file_path: Path) -> Tuple[str, List[PatchResult]]:
        """Transforms smali source code according to matched rules."""
        results: List[PatchResult] = []
        new_content = content
        class_desc = self._extract_class_desc(new_content)

        for rule in self.rules:
            # Check class match
            if not self._class_matches(rule, class_desc, file_path):
                continue

            if rule.target_method:
                new_content, res = self._apply_method_rule(new_content, rule, file_path)
                if res:
                    results.append(res)
            elif rule.target_signature:
                new_content, res = self._apply_line_signature_rule(new_content, rule, file_path)
                if res:
                    results.append(res)

        return new_content, results

    def _class_matches(self, rule: PatchRule, class_desc: str, file_path: Path) -> bool:
        if rule.target_class_pattern == ".*":
            return True
        if re.search(rule.target_class_pattern, class_desc, re.IGNORECASE):
            return True
        if re.search(rule.target_class_pattern, file_path.name, re.IGNORECASE):
            return True
        return False

    def _extract_class_desc(self, content: str) -> str:
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith(".class"):
                m = CLASS_DEF_REGEX.search(line_str)
                if m:
                    return m.group(1)
        return ""

    def _apply_method_rule(
        self, content: str, rule: PatchRule, file_path: Path
    ) -> Tuple[str, Optional[PatchResult]]:
        lines = content.splitlines()
        output_lines: List[str] = []
        in_target_method = False
        method_lines: List[str] = []
        method_name = ""
        changes_count = 0
        diff_text = None

        for line in lines:
            stripped = line.strip()
            m_def = METHOD_DEF_REGEX.match(stripped)

            if m_def:
                candidate_name = m_def.group("name")
                if re.search(f"^(?:{rule.target_method})$", candidate_name):
                    in_target_method = True
                    method_name = candidate_name
                    method_lines = [line]
                    continue

            if in_target_method:
                method_lines.append(line)
                if END_METHOD_REGEX.match(stripped):
                    in_target_method = False
                    orig_method_block = "\n".join(method_lines)
                    patched_method_block = self._generate_stubbed_method(
                        method_lines, rule.strategy, rule.replacement_instructions
                    )

                    if orig_method_block != patched_method_block:
                        changes_count += 1
                        diff_text = "\n".join(
                            difflib.unified_diff(
                                orig_method_block.splitlines(),
                                patched_method_block.splitlines(),
                                fromfile=f"a/{file_path.name}",
                                tofile=f"b/{file_path.name}",
                                lineterm="",
                            )
                        )
                    output_lines.extend(patched_method_block.splitlines())
                    method_lines = []
                continue

            output_lines.append(line)

        new_content = "\n".join(output_lines)
        if changes_count > 0:
            result = PatchResult(
                file_path=file_path,
                rule_id=rule.rule_id,
                success=True,
                changes_made=changes_count,
                message=f"Stubbed method '{method_name}' using strategy '{rule.strategy.value}'",
                diff=diff_text,
            )
            return new_content, result

        return content, None

    def _generate_stubbed_method(
        self,
        method_lines: List[str],
        strategy: PatchStrategy,
        custom_instructions: Optional[List[str]] = None,
    ) -> str:
        """Generates a clean stubbed replacement method body."""
        header_line = method_lines[0]
        end_line = method_lines[-1]

        # Preserve annotations if any
        annotations: List[str] = []
        in_annotation = False
        for l in method_lines[1:-1]:
            s = l.strip()
            if s.startswith(".annotation"):
                in_annotation = True
                annotations.append(l)
            elif in_annotation:
                annotations.append(l)
                if s.startswith(".end annotation"):
                    in_annotation = False

        stub_body: List[str] = []

        if custom_instructions:
            stub_body = custom_instructions
        elif strategy == PatchStrategy.STUB_RETURN_VOID:
            stub_body = [
                "    .locals 0",
                "",
                "    # [PATCHED: Ad/tamper routine stubbed]",
                "    return-void",
            ]
        elif strategy == PatchStrategy.STUB_RETURN_BOOL_TRUE:
            stub_body = [
                "    .locals 1",
                "",
                "    # [PATCHED: Integrity check forced true]",
                "    const/4 v0, 0x1",
                "    return v0",
            ]
        elif strategy == PatchStrategy.STUB_RETURN_BOOL_FALSE:
            stub_body = [
                "    .locals 1",
                "",
                "    # [PATCHED: Feature forced false]",
                "    const/4 v0, 0x0",
                "    return v0",
            ]
        else:
            return "\n".join(method_lines)

        result_lines = [header_line]
        if annotations:
            result_lines.extend(annotations)
        result_lines.extend(stub_body)
        result_lines.append(end_line)
        return "\n".join(result_lines)

    def _apply_line_signature_rule(
        self, content: str, rule: PatchRule, file_path: Path
    ) -> Tuple[str, Optional[PatchResult]]:
        lines = content.splitlines()
        output_lines: List[str] = []
        changes = 0

        for line in lines:
            stripped = line.strip()
            if re.search(rule.target_signature, stripped) and not stripped.startswith("#"):
                indent = line[: len(line) - len(line.lstrip())]
                commented_line = f"{indent}# [PATCHED: neutralized] {stripped}"
                output_lines.append(commented_line)
                changes += 1
            else:
                output_lines.append(line)

        if changes > 0:
            diff_text = "\n".join(
                difflib.unified_diff(
                    lines, output_lines, fromfile=f"a/{file_path.name}", tofile=f"b/{file_path.name}", lineterm=""
                )
            )
            return "\n".join(output_lines), PatchResult(
                file_path=file_path,
                rule_id=rule.rule_id,
                success=True,
                changes_made=changes,
                message=f"Neutralized {changes} matching signature line(s)",
                diff=diff_text,
            )

        return content, None
