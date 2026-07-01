#!/usr/bin/env python3
"""校验 manifest.jsonl 与 raw 目录一致性。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weekly QC for raw data lake")
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = args.manifest or (args.raw_root / "manifest.jsonl")
    if not manifest.exists():
        raise FileNotFoundError(manifest)

    missing = 0
    total = 0
    with manifest.open() as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            rec = json.loads(line)
            ep_dir = args.raw_root / rec["path"]
            if not ep_dir.exists():
                print(f"line {line_no}: MISSING {ep_dir}")
                missing += 1

    print(f"checked {total} manifest records, missing={missing}")
    if missing:
        raise SystemExit(1)
    print("QC passed")


if __name__ == "__main__":
    main()
