#!/usr/bin/env python3
"""Apply a locale's translations to Localizable.xcstrings from JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def entry(value: str) -> dict:
    return {"stringUnit": {"state": "translated", "value": value}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True, help="Path to Localizable.xcstrings")
    parser.add_argument("--locale", required=True, help="BCP-47 locale code, e.g. ja, ko, fr")
    parser.add_argument("--translations", type=Path, required=True, help="JSON dict: key → translated string")
    parser.add_argument("--settings-key", help="Optional settings_language_* key to ensure exists")
    parser.add_argument("--labels", type=Path, help="JSON dict: locale → label for settings-key")
    args = parser.parse_args()

    if not args.catalog.is_file():
        print(f"ERROR: catalog not found: {args.catalog}", file=sys.stderr)
        return 1
    if not args.translations.is_file():
        print(f"ERROR: translations not found: {args.translations}", file=sys.stderr)
        return 1

    translations: dict[str, str] = json.loads(args.translations.read_text(encoding="utf-8"))
    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    strings = data["strings"]
    added = 0
    locale = args.locale

    for key, item in strings.items():
        localizations = item.setdefault("localizations", {})
        if locale in localizations:
            continue
        if key not in translations:
            raise KeyError(f"Missing {locale} translation for key: {key}")
        localizations[locale] = entry(translations[key])
        added += 1

    if args.settings_key:
        if args.settings_key not in strings:
            strings[args.settings_key] = {"localizations": {}}
        locs = strings[args.settings_key].setdefault("localizations", {})
        if args.labels and args.labels.is_file():
            labels = json.loads(args.labels.read_text(encoding="utf-8"))
            for loc_code, label in labels.items():
                locs.setdefault(loc_code, entry(label))
        elif locale not in locs and args.settings_key in translations:
            locs.setdefault(locale, entry(translations[args.settings_key]))

    args.catalog.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {added} {locale} entries in {args.catalog}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
