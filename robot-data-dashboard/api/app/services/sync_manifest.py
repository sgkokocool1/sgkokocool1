"""从 manifest.jsonl 与文件系统同步统计数据到数据库。"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import DailyStat, Episode, EpisodeStage, StorageSnapshot


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compute_stage(rec: dict, staging_paths: set[str], validation_failed: set[str]) -> EpisodeStage:
    path = rec["path"]
    if path in staging_paths:
        return EpisodeStage.staging
    if path in validation_failed:
        return EpisodeStage.validation_failed
    if rec.get("imported_to"):
        return EpisodeStage.imported
    if rec.get("success"):
        return EpisodeStage.pending_import
    return EpisodeStage.raw_archived


def scan_staging_paths(data_root: Path) -> set[str]:
    staging = data_root / "staging" / "today"
    paths: set[str] = set()
    if not staging.exists():
        return paths
    for session_dir in staging.iterdir():
        if not session_dir.is_dir():
            continue
        for ep_dir in session_dir.glob("episode_*"):
            if ep_dir.is_dir():
                rel = ep_dir.relative_to(data_root / "raw") if (data_root / "raw") in ep_dir.parents else None
                # staging paths are not under raw yet; use tentative key session/episode
                paths.add(f"__staging__/{session_dir.name}/{ep_dir.name}")
    return paths


def load_validation_failed(data_root: Path) -> set[str]:
    failed: set[str] = set()
    raw = data_root / "raw"
    if not raw.exists():
        return failed
    for validation in raw.glob("**/validation.json"):
        try:
            data = json.loads(validation.read_text())
            if not data.get("valid", True):
                ep_dir = validation.parent
                try:
                    rel = ep_dir.relative_to(raw)
                    failed.add(str(rel).replace("\\", "/"))
                except ValueError:
                    pass
        except (json.JSONDecodeError, OSError):
            continue
    return failed


def load_episode_meta(data_root: Path, path: str) -> dict:
    meta_path = data_root / "raw" / path / "episode_meta.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def sync_manifest(db: Session, data_root: Path | None = None) -> int:
    settings = get_settings()
    root = data_root or settings.data_root
    manifest_path = root / "raw" / "manifest.jsonl"
    if not manifest_path.exists():
        return 0

    validation_failed = load_validation_failed(root)
    staging_paths: set[str] = set()  # staging episodes not in manifest yet
    synced = 0

    with manifest_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            path = rec["path"]
            meta = load_episode_meta(root, path)
            stage = compute_stage(rec, staging_paths, validation_failed)

            values = {
                "path": path,
                "collect_date": _parse_date(rec["date"]),
                "session_key": rec["session"],
                "episode_name": rec["episode"],
                "source": rec.get("source", "ros"),
                "task": rec.get("task", ""),
                "success": bool(rec.get("success", False)),
                "fps": int(rec.get("fps", 30)),
                "frames": int(rec.get("frames", 0)),
                "duration_sec": meta.get("duration_sec"),
                "operator": meta.get("operator"),
                "robot_id": meta.get("robot_id"),
                "stage": stage,
                "imported_to": rec.get("imported_to"),
                "imported_at": _parse_dt(rec.get("imported_at")),
                "validation_ok": path not in validation_failed if validation_failed else None,
                "meta_json": meta or None,
                "updated_at": datetime.now(timezone.utc),
            }

            stmt = insert(Episode).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Episode.path],
                set_={k: v for k, v in values.items() if k != "path"},
            )
            db.execute(stmt)
            synced += 1

    db.commit()
    return synced


def rebuild_daily_stats(db: Session, days: int = 90) -> int:
    db.execute(delete(DailyStat))
    db.commit()

    rows = db.execute(
        select(
            Episode.collect_date,
            Episode.source,
            func.count().label("episodes_total"),
            func.count().filter(Episode.success.is_(True)).label("episodes_success"),
            func.count().filter(Episode.success.is_(False)).label("episodes_failed"),
            func.coalesce(func.sum(Episode.frames), 0).label("frames_total"),
            func.count().filter(Episode.imported_to.isnot(None)).label("episodes_imported"),
            func.count().filter(Episode.success.is_(True), Episode.imported_to.is_(None)).label("episodes_pending"),
        ).group_by(Episode.collect_date, Episode.source)
    ).all()

    count = 0
    for row in rows:
        db.add(
            DailyStat(
                stat_date=row.collect_date,
                source=row.source,
                task="_all",
                episodes_total=row.episodes_total,
                episodes_success=row.episodes_success,
                episodes_failed=row.episodes_failed,
                frames_total=int(row.frames_total),
                episodes_imported=row.episodes_imported,
                episodes_pending=row.episodes_pending,
            )
        )
        count += 1
    db.commit()
    return count


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def snapshot_storage(db: Session, data_root: Path | None = None) -> StorageSnapshot:
    settings = get_settings()
    root = data_root or settings.data_root
    snap = StorageSnapshot(
        raw_bytes=dir_size(root / "raw"),
        staging_bytes=dir_size(root / "staging"),
        lerobot_bytes=dir_size(root / "lerobot"),
        training_bytes=dir_size(root / "training"),
        builds_bytes=dir_size(root / "builds"),
        details_json={
            "raw": str(root / "raw"),
            "staging": str(root / "staging"),
            "lerobot": str(root / "lerobot"),
        },
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap
