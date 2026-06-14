#!/usr/bin/env python3
"""Audit Localizable.xcstrings for locale coverage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--locale", action="append", help="Check specific locale(s); default all found")
    args = parser.parse_args()

    if not args.catalog.is_file():
        print(f"ERROR: not found: {args.catalog}", file=sys.stderr)
        return 1

    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    strings = data["strings"]

    all_locales: set[str] = set()
    for item in strings.values():
        all_locales.update(item.get("localizations", {}).keys())

    check_locales = set(args.locale) if args.locale else all_locales
    if not check_locales:
        print("No localizations found in catalog.")
        return 1

    print(f"Catalog: {args.catalog}")
    print(f"Total keys: {len(strings)}")
    print(f"Locales: {', '.join(sorted(all_locales))}\n")

    failed = False
    for loc in sorted(check_locales):
        missing = [
            k for k, v in strings.items()
            if v.get("localizations") and loc not in v.get("localizations", {})
        ]
        status = "OK" if not missing else "INCOMPLETE"
        print(f"[{status}] {loc}: {len(strings) - len(missing)}/{len(strings)} complete, missing {len(missing)}")
        if missing[:5]:
            print(f"  examples: {', '.join(missing[:5])}")
        if missing:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
