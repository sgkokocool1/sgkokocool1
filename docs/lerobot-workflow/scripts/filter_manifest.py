#!/usr/bin/env python3
"""从 manifest.jsonl 按日期范围筛选 episode，生成 import_list.jsonl。"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter manifest.jsonl by date range")
    parser.add_argument("--input", type=Path, required=True, help="全量 manifest.jsonl")
    parser.add_argument("--output", type=Path, required=True, help="输出 import_list.jsonl")
    parser.add_argument("--date-from", required=True, help="起始日期 YYYY-MM-DD")
    parser.add_argument("--date-to", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--success-only", action="store_true", help="只保留 success=true")
    parser.add_argument("--task", default=None, help="可选：按任务名过滤")
    parser.add_argument("--source", default=None, help="可选：按来源过滤 ros/sim/mp4")
    return parser.parse_args()


def in_date_range(rec_date: str, d_from: date, d_to: date) -> bool:
    d = date.fromisoformat(rec_date)
    return d_from <= d <= d_to


def main() -> None:
    args = parse_args()
    d_from = date.fromisoformat(args.date_from)
    d_to = date.fromisoformat(args.date_to)

    selected: list[dict] = []
    with args.input.open() as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if not in_date_range(rec["date"], d_from, d_to):
                continue
            if args.success_only and not rec.get("success", False):
                continue
            if args.task and rec.get("task") != args.task:
                continue
            if args.source and rec.get("source") != args.source:
                continue
            selected.append(rec)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as f:
        for rec in selected:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"selected {len(selected)} episodes → {args.output}")


if __name__ == "__main__":
    main()
