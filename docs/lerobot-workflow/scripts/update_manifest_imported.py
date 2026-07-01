#!/usr/bin/env python3
"""构建完成后，更新 manifest.jsonl 中被导入 episode 的 imported_to 字段。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update imported_to in manifest.jsonl")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--import-list", type=Path, required=True, help="本次导入的 import_list.jsonl")
    parser.add_argument("--dataset-id", required=True, help='如 "local/pick-place-w2-202507"')
    return parser.parse_args()


def load_paths(import_list: Path) -> set[str]:
    paths: set[str] = set()
    with import_list.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            paths.add(rec["path"])
    return paths


def main() -> None:
    args = parse_args()
    imported_paths = load_paths(args.import_list)
    now = datetime.now(timezone.utc).isoformat()

    records: list[dict] = []
    updated = 0
    with args.manifest.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("path") in imported_paths:
                rec["imported_to"] = args.dataset_id
                rec["imported_at"] = now
                updated += 1
            records.append(rec)

    with args.manifest.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"updated {updated} records in {args.manifest} → imported_to={args.dataset_id}")


if __name__ == "__main__":
    main()
