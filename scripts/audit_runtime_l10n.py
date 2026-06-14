#!/usr/bin/env python3
"""Audit Swift sources for common runtime localization pitfalls."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    severity: str  # WARN | INFO
    category: str
    path: Path
    line: int
    message: str


CJK_RE = re.compile(r"[\u4e00-\u9fff]")
PERSIST_RE = re.compile(
    r"UserDefaults|@AppStorage|\.set\(|\.string\(forKey|Codable|JSONEncoder|JSONDecoder",
    re.IGNORECASE,
)
SEED_RE = re.compile(
    r"defaultHabits|seedData|initialData|default.*=\s*\[|=\s*\[[^\]]*\"",
    re.IGNORECASE,
)
NAV_TITLE_RE = re.compile(r"\.navigationTitle\s*\(\s*\"([^\"]+)\"")
TAB_RE = re.compile(r"\.tabItem\s*\{|Tab\s*\(\s*\"([^\"]+)\"")
LOCALE_ENV_RE = re.compile(r"\.environment\s*\(\s*\\\.locale")
ID_LANG_RE = re.compile(r"\.id\s*\(\s*.*[Ll]anguage")
EXPLICIT_LOCALIZED_RE = re.compile(
    r"String\s*\(\s*localized:|AppLocalization\.|LocalizedStringKey\s*\("
)


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        findings.append(Finding("WARN", "io", path, 0, str(exc)))
        return findings

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue

        if PERSIST_RE.search(line) and CJK_RE.search(line):
            findings.append(
                Finding(
                    "WARN",
                    "persisted_localized_string",
                    path,
                    i,
                    "Possible localized display string near persistence API",
                )
            )

        if SEED_RE.search(line) and CJK_RE.search(line):
            findings.append(
                Finding(
                    "WARN",
                    "seed_data_localized",
                    path,
                    i,
                    "Default/seed data may store locale-specific display strings",
                )
            )

        nav = NAV_TITLE_RE.search(line)
        if nav and "." in nav.group(1):
            findings.append(
                Finding(
                    "WARN",
                    "navigation_title_key",
                    path,
                    i,
                    f"navigationTitle uses key literal '{nav.group(1)}' — may not refresh on in-app language switch",
                )
            )

        tab = TAB_RE.search(line)
        if tab and tab.lastindex and "." in tab.group(1):
            findings.append(
                Finding(
                    "INFO",
                    "tab_title_key",
                    path,
                    i,
                    f"Tab label uses key literal '{tab.group(1)}' — verify runtime refresh",
                )
            )

    return findings


def scan_project(swift_files: list[Path]) -> list[Finding]:
    """Project-level checks run once across all sources."""
    findings: list[Finding] = []
    has_locale_env = False
    has_id_lang = False
    has_explicit_l10n = False

    for path in swift_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if LOCALE_ENV_RE.search(text):
            has_locale_env = True
        if ID_LANG_RE.search(text):
            has_id_lang = True
        if EXPLICIT_LOCALIZED_RE.search(text):
            has_explicit_l10n = True

    root = swift_files[0].parent if swift_files else Path(".")
    if not has_locale_env and not has_explicit_l10n:
        findings.append(
            Finding(
                "INFO",
                "missing_locale_environment",
                root,
                0,
                "No .environment(\\.locale) or explicit String(localized:) found — verify if in-app switch is supported",
            )
        )
    if not has_id_lang:
        findings.append(
            Finding(
                "INFO",
                "missing_view_refresh",
                root,
                0,
                "No .id(...Language) found — SwiftUI views may not refresh after language change",
            )
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="Swift source root (e.g. MyApp/)")
    parser.add_argument("--glob", default="*.swift", help="File glob under source-dir")
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        print(f"ERROR: not a directory: {args.source_dir}", file=sys.stderr)
        return 1

    swift_files = sorted(args.source_dir.rglob(args.glob))
    if not swift_files:
        print(f"No Swift files under {args.source_dir}")
        return 1

    all_findings: list[Finding] = []
    for path in swift_files:
        if "Tests" in path.parts or "UITests" in path.parts:
            continue
        all_findings.extend(scan_file(path))

    all_findings.extend(scan_project(swift_files))

    warns = [f for f in all_findings if f.severity == "WARN"]
    infos = [f for f in all_findings if f.severity == "INFO"]

    print(f"Source: {args.source_dir}")
    print(f"Scanned: {len(swift_files)} Swift files")
    print(f"WARN: {len(warns)}  INFO: {len(infos)}\n")

    for f in warns + infos:
        loc = f"{f.path}:{f.line}" if f.line else str(f.path)
        print(f"[{f.severity}] {f.category} @ {loc}")
        print(f"  {f.message}")

    if warns:
        print("\nFix guidance: platforms/ios-swift.md §9, reference.md § 持久化数据本地化")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
