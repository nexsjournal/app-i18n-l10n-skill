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
APPLE_LANG_RE = re.compile(r"AppleLanguages")
APP_L10N_RE = re.compile(r"AppLocalization\.|enum\s+AppLocalization")
EXPLICIT_LOCALIZED_RE = re.compile(
    r"String\s*\(\s*localized:|LocalizedStringKey\s*\("
)
LOCALIZED_KEY_UI_RE = re.compile(
    r"(?:Text|Toggle|Label|Button)\s*\(\s*\"([a-z][a-z0-9_.]+)\""
)
DISPLAY_NAME_RE = re.compile(r"(?:var|func)\s+displayName")
DATE_FORMATTER_RE = re.compile(r"DateFormatter\s*\(")
EXPORT_RE = re.compile(r"ExportService|export.*[Ff]ormat|share.*[Tt]ext")


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        findings.append(Finding("WARN", "io", path, 0, str(exc)))
        return findings

    text = "\n".join(lines)

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
                    f"navigationTitle uses key '{nav.group(1)}' — use AppLocalization or verify L1/L3 refresh",
                )
            )

        ui_key = LOCALIZED_KEY_UI_RE.search(line)
        if ui_key and "." in ui_key.group(1):
            findings.append(
                Finding(
                    "INFO",
                    "localized_string_key_ui",
                    path,
                    i,
                    f"LocalizedStringKey '{ui_key.group(1)}' — requires AppleLanguages (L1) to follow in-app language",
                )
            )

        if DISPLAY_NAME_RE.search(line):
            block = "\n".join(lines[i - 1 : min(i + 8, len(lines))])
            if CJK_RE.search(block) and "AppLocalization" not in block:
                findings.append(
                    Finding(
                        "WARN",
                        "display_name_hardcoded",
                        path,
                        i,
                        "displayName may return hardcoded locale-specific text — use AppLocalization + key (L2)",
                    )
                )

        if DATE_FORMATTER_RE.search(line):
            block = "\n".join(lines[i - 1 : min(i + 5, len(lines))])
            if ".locale" not in block and "resolvedLocale" not in block:
                findings.append(
                    Finding(
                        "INFO",
                        "date_formatter_locale",
                        path,
                        i,
                        "DateFormatter may use system locale — bind settings.resolvedLocale (L3)",
                    )
                )

    if EXPORT_RE.search(text) and APP_L10N_RE.search(text) is None and CJK_RE.search(text):
        findings.append(
            Finding(
                "INFO",
                "export_without_l10n",
                path,
                0,
                "Export/share formatting may need AppLocalization for dynamic strings (L2)",
            )
        )

    return findings


def scan_project(swift_files: list[Path], require_in_app: bool) -> list[Finding]:
    """Project-level checks run once across all sources."""
    findings: list[Finding] = []
    has_locale_env = False
    has_id_lang = False
    has_apple_lang = False
    has_app_l10n = False
    has_app_language = False
    has_localized_key_ui = False

    for path in swift_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if LOCALE_ENV_RE.search(text):
            has_locale_env = True
        if ID_LANG_RE.search(text):
            has_id_lang = True
        if APPLE_LANG_RE.search(text):
            has_apple_lang = True
        if APP_L10N_RE.search(text):
            has_app_l10n = True
        if re.search(r"enum\s+AppLanguage|appLanguage", text):
            has_app_language = True
        if LOCALIZED_KEY_UI_RE.search(text):
            has_localized_key_ui = True

    root = swift_files[0].parent if swift_files else Path(".")

    if require_in_app or has_app_language:
        if not has_app_language:
            findings.append(
                Finding(
                    "WARN",
                    "missing_app_language",
                    root,
                    0,
                    "in_app_switch expected but no AppLanguage enum — only system language will work",
                )
            )
        if has_localized_key_ui and not has_apple_lang:
            findings.append(
                Finding(
                    "WARN",
                    "missing_apple_languages",
                    root,
                    0,
                    "Text/Toggle use LocalizedStringKey but AppleLanguages not set — L1 chain incomplete",
                )
            )
        if not has_app_l10n:
            findings.append(
                Finding(
                    "INFO",
                    "missing_app_localization",
                    root,
                    0,
                    "No AppLocalization helper — dynamic keys (mood/habit/export) may not translate (L2)",
                )
            )

    if require_in_app or has_app_language:
        if not has_locale_env:
            findings.append(
                Finding(
                    "INFO",
                    "missing_locale_environment",
                    root,
                    0,
                    "No .environment(\\.locale) on root — date/number formatting may be wrong (L3)",
                )
            )
        if not has_id_lang:
            findings.append(
                Finding(
                    "INFO",
                    "missing_view_refresh",
                    root,
                    0,
                    "No .id(...Language) — nested views may not refresh after language change (L3)",
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="Swift source root (e.g. MyApp/)")
    parser.add_argument("--glob", default="*.swift", help="File glob under source-dir")
    parser.add_argument(
        "--require-in-app-switch",
        action="store_true",
        help="Stricter checks for in_app_switch projects (AppLanguage, AppleLanguages, etc.)",
    )
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        print(f"ERROR: not a directory: {args.source_dir}", file=sys.stderr)
        return 1

    swift_files = sorted(args.source_dir.rglob(args.glob))
    if not swift_files:
        print(f"No Swift files under {args.source_dir}")
        return 1

    app_files = [p for p in swift_files if "Tests" not in p.parts and "UITests" not in p.parts]

    all_findings: list[Finding] = []
    for path in app_files:
        all_findings.extend(scan_file(path))

    all_findings.extend(scan_project(app_files, args.require_in_app_switch))

    warns = [f for f in all_findings if f.severity == "WARN"]
    infos = [f for f in all_findings if f.severity == "INFO"]

    print(f"Source: {args.source_dir}")
    print(f"Scanned: {len(app_files)} Swift files")
    print(f"WARN: {len(warns)}  INFO: {len(infos)}\n")

    for f in warns + infos:
        loc = f"{f.path}:{f.line}" if f.line else str(f.path)
        print(f"[{f.severity}] {f.category} @ {loc}")
        print(f"  {f.message}")

    if warns:
        print("\nFix guidance: platforms/ios-swift.md §3.1 & §9 (L1 AppleLanguages, L2 AppLocalization, L3 refresh)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
