#!/usr/bin/env python3
"""从 manifest.jsonl 同步统计数据到 PostgreSQL。可由 cron 或 ingest/build 钩子调用。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许从 api 目录运行
API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.database import SessionLocal  # noqa: E402
from app.services.jobs import record_job  # noqa: E402
from app.services.sync_manifest import rebuild_daily_stats, snapshot_storage, sync_manifest  # noqa: E402
from app.schemas import RecordJobRequest  # noqa: E402
from app.config import get_settings  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync robot raw data stats to dashboard DB")
    p.add_argument("--data-root", type=Path, default=None)
    p.add_argument("--event", choices=["full", "ingest", "build"], default="full")
    p.add_argument("--job-type", default=None)
    p.add_argument("--report", type=Path, default=None, help="import_report.json path")
    p.add_argument("--status", default="success")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    data_root = args.data_root or settings.data_root

    db = SessionLocal()
    try:
        n = sync_manifest(db, data_root)
        rebuild_daily_stats(db)
        snap = snapshot_storage(db, data_root)
        print(f"synced episodes={n} storage_snapshot_id={snap.id}")

        if args.event in ("ingest", "build") and args.job_type:
            report = {}
            if args.report and args.report.exists():
                import json

                report = json.loads(args.report.read_text())
            record_job(
                db,
                RecordJobRequest(
                    job_type=args.job_type,
                    status=args.status,
                    report_json=report or None,
                    episodes_ok=report.get("imported_episodes", 0),
                    episodes_fail=report.get("skipped_in_range", 0),
                    frames_in=report.get("total_frames", 0),
                ),
            )
            print(f"recorded job type={args.job_type}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
