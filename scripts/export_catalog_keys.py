#!/usr/bin/env python3
"""Export localization keys from Localizable.xcstrings to JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--source-locale", default="en", help="Locale to use as reference values")
    args = parser.parse_args()

    if not args.catalog.is_file():
        print(f"ERROR: not found: {args.catalog}", file=sys.stderr)
        return 1

    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    items = []
    for key in sorted(data["strings"].keys()):
        locs = data["strings"][key].get("localizations", {})
        ref = locs.get(args.source_locale, {}).get("stringUnit", {}).get("value", "")
        zh = locs.get("zh-Hans", {}).get("stringUnit", {}).get("value", "")
        items.append({"key": key, "reference": ref, "zh-Hans": zh})

    args.output.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(items)} keys to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
