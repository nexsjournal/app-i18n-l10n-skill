#!/usr/bin/env python3
"""Validate App Store Connect metadata character limits in localization deliverables."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

LIMITS = {
    "app_name": 30,
    "subtitle": 30,
    "promotional_text": 170,
    "description": 4000,
    "keywords": 100,
    "whats_new": 4000,
}

# Heading text (without # prefix) → field key
SECTION_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"App\s*名称|App\s*Name", re.I), "app_name"),
    (re.compile(r"副标题|Subtitle", re.I), "subtitle"),
    (re.compile(r"推广文本|Promotional\s*Text", re.I), "promotional_text"),
    (re.compile(r"描述|Description", re.I), "description"),
    (re.compile(r"关键词|Keywords", re.I), "keywords"),
    (re.compile(r"此版本|What's\s*New|What.s\s*New", re.I), "whats_new"),
]


@dataclass
class FieldResult:
    name: str
    limit: int
    length: int
    ok: bool
    preview: str


def find_field_content(text: str, field_key: str) -> str | None:
    """Return first ```text block after a matching section heading."""
    lines = text.splitlines()
    in_section = False
    section_level = 0

    for i, line in enumerate(lines):
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line.lstrip("#").strip()
            matched = any(p.search(heading) for p, key in SECTION_MAP if key == field_key)
            if matched:
                in_section = True
                section_level = level
                continue
            if in_section and level <= section_level:
                in_section = False

        if in_section and line.strip().startswith("```"):
            block_start = i + 1
            block_lines: list[str] = []
            for j in range(block_start, len(lines)):
                if lines[j].strip() == "```":
                    return "\n".join(block_lines).strip()
                block_lines.append(lines[j])
    return None


def validate_keywords(text: str) -> list[str]:
    issues: list[str] = []
    parts = [p.strip() for p in text.split(",") if p.strip()]
    seen: set[str] = set()
    for part in parts:
        lower = part.lower()
        if lower in seen:
            issues.append(f"duplicate keyword: {part}")
        seen.add(lower)
    if ", " in text:
        issues.append("keywords contain comma+space; use comma without spaces")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True, help="Metadata markdown file")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        return 1

    content = args.file.read_text(encoding="utf-8")
    results: list[FieldResult] = []
    failed = False

    print(f"Validating: {args.file}\n")

    for field_key, limit in LIMITS.items():
        value = find_field_content(content, field_key)
        if value is None:
            print(f"⚠️  SKIP  {field_key}: section not found")
            continue

        length = len(value)
        ok = length <= limit
        preview = value.replace("\n", " ")[:60] + ("…" if len(value) > 60 else "")
        results.append(FieldResult(field_key, limit, length, ok, preview))

        status = "✅" if ok else "❌"
        print(f"{status}  {field_key}: {length}/{limit}")
        if not ok:
            failed = True
            print(f"     over by {length - limit} characters")

        if field_key == "keywords":
            for issue in validate_keywords(value):
                print(f"❌  keywords: {issue}")
                failed = True

    print()
    if failed:
        print("FAILED — fix over-limit fields before submitting to App Store Connect.")
        return 1

    if not results:
        print("WARNING — no fields extracted; check markdown structure.")
        return 1

    print("OK — all extracted fields within limits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
