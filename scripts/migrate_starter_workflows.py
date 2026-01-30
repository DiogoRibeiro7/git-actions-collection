#!/usr/bin/env python3
"""Migrate GitHub starter workflows to this collection's reusable workflows."""
from __future__ import annotations

import argparse
import os
import sys

from scripts._lib.workflows import convert, detect_language, generate_migrated as generate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", help="Path to GitHub starter workflow")
    parser.add_argument(
        "--output", "-o", help="Where to write converted workflow (stdout if omitted)"
    )
    args = parser.parse_args()

    with open(args.workflow, "r", encoding="utf-8") as fh:
        content = fh.read()

    migrated = convert(content)

    if args.output:
        if os.path.exists(args.output):
            raise SystemExit(f"Refusing to overwrite existing file: {args.output}")
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(migrated)
    else:
        sys.stdout.write(migrated)


if __name__ == "__main__":
    main()
