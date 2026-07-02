from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Episode, ProcessingJob, StorageSnapshot
from app.schemas import (
    DailyTrendPoint,
    DailyTrendResponse,
    DistributionItem,
    DistributionResponse,
    EpisodeItem,
    EpisodeListResponse,
    EpisodeMetrics,
    FunnelResponse,
    FunnelStage,
    JobItem,
    JobListResponse,
    JobsSummary,
    OverviewResponse,
    SourceBreakdown,
    StoragePoint,
    StorageResponse,
    StorageSummary,
)

STAGE_LABELS = {
    "staging": "待日终归档",
    "raw_archived": "已归档 raw",
    "validation_failed": "校验失败",
    "pending_import": "待构建导入",
    "imported": "已入数据集",
    "skipped": "已跳过",
}


def _bytes_to_gb(n: int | None) -> float:
    if not n:
        return 0.0
    return round(n / (1024**3), 2)


def get_overview(db: Session) -> OverviewResponse:
    total = db.scalar(select(func.count()).select_from(Episode)) or 0
    success = db.scalar(select(func.count()).select_from(Episode).where(Episode.success.is_(True))) or 0
    failed = total - success
    imported = db.scalar(select(func.count()).select_from(Episode).where(Episode.imported_to.isnot(None))) or 0
    pending = db.scalar(
        select(func.count()).select_from(Episode).where(Episode.success.is_(True), Episode.imported_to.is_(None))
    ) or 0
    frames = db.scalar(select(func.coalesce(func.sum(Episode.frames), 0))) or 0

    by_source: dict[str, SourceBreakdown] = {}
    rows = db.execute(
        select(
            Episode.source,
            func.count(),
            func.count().filter(Episode.success.is_(True)),
            func.count().filter(Episode.success.is_(False)),
            func.count().filter(Episode.imported_to.isnot(None)),
            func.coalesce(func.sum(Episode.frames), 0),
        ).group_by(Episode.source)
    ).all()
    for source, t, s, f, imp, fr in rows:
        by_source[source] = SourceBreakdown(total=t, success=s, failed=f, imported=imp, frames=int(fr))

    since = datetime.now(timezone.utc) - timedelta(days=7)
    jobs_total = db.scalar(select(func.count()).select_from(ProcessingJob).where(ProcessingJob.started_at >= since)) or 0
    jobs_ok = (
        db.scalar(
            select(func.count())
            .select_from(ProcessingJob)
            .where(ProcessingJob.started_at >= since, ProcessingJob.status == "success")
        )
        or 0
    )
    jobs_fail = jobs_total - jobs_ok

    latest_storage = db.scalar(select(StorageSnapshot).order_by(StorageSnapshot.snapshot_at.desc()).limit(1))
    storage = StorageSummary()
    if latest_storage:
        storage = StorageSummary(
            raw_gb=_bytes_to_gb(latest_storage.raw_bytes),
            staging_gb=_bytes_to_gb(latest_storage.staging_bytes),
            lerobot_gb=_bytes_to_gb(latest_storage.lerobot_bytes),
            training_gb=_bytes_to_gb(latest_storage.training_bytes),
        )

    return OverviewResponse(
        episodes=EpisodeMetrics(
            total=total,
            success=success,
            failed=failed,
            success_rate=round(success / total, 4) if total else 0.0,
            imported=imported,
            pending=pending,
            frames_total=int(frames),
        ),
        by_source=by_source,
        jobs_7d=JobsSummary(total=jobs_total, success=jobs_ok, failed=jobs_fail),
        storage=storage,
        updated_at=datetime.now(timezone.utc),
    )


def get_funnel(db: Session) -> FunnelResponse:
    rows = db.execute(select(Episode.stage, func.count()).group_by(Episode.stage)).all()
    counts = {stage.value if hasattr(stage, "value") else str(stage): c for stage, c in rows}
    order = ["staging", "raw_archived", "validation_failed", "pending_import", "imported", "skipped"]
    stages = [
        FunnelStage(name=name, label=STAGE_LABELS.get(name, name), count=counts.get(name, 0)) for name in order
    ]
    return FunnelResponse(stages=stages)


def get_distribution_by_source(db: Session) -> DistributionResponse:
    rows = db.execute(
        select(
            Episode.source,
            func.count(),
            func.count().filter(Episode.success.is_(True)),
            func.count().filter(Episode.success.is_(False)),
            func.count().filter(Episode.imported_to.isnot(None)),
            func.coalesce(func.sum(Episode.frames), 0),
        ).group_by(Episode.source)
    ).all()
    items = [
        DistributionItem(key=src, total=t, success=s, failed=f, imported=imp, frames=int(fr))
        for src, t, s, f, imp, fr in rows
    ]
    return DistributionResponse(items=items)


def get_distribution_by_task(db: Session) -> DistributionResponse:
    rows = db.execute(
        select(
            Episode.task,
            func.count(),
            func.count().filter(Episode.success.is_(True)),
            func.count().filter(Episode.success.is_(False)),
            func.count().filter(Episode.imported_to.isnot(None)),
            func.coalesce(func.sum(Episode.frames), 0),
        ).group_by(Episode.task)
    ).all()
    items = [
        DistributionItem(key=task, total=t, success=s, failed=f, imported=imp, frames=int(fr))
        for task, t, s, f, imp, fr in rows
    ]
    return DistributionResponse(items=items)


def get_daily_trend(db: Session, date_from=None, date_to=None) -> DailyTrendResponse:
    q = select(
        Episode.collect_date,
        func.count(),
        func.count().filter(Episode.success.is_(True)),
        func.count().filter(Episode.success.is_(False)),
        func.count().filter(Episode.imported_to.isnot(None)),
    ).group_by(Episode.collect_date)
    if date_from:
        q = q.where(Episode.collect_date >= date_from)
    if date_to:
        q = q.where(Episode.collect_date <= date_to)
    rows = db.execute(q.order_by(Episode.collect_date)).all()
    points = [DailyTrendPoint(date=d, total=t, success=s, failed=f, imported=imp) for d, t, s, f, imp in rows]
    return DailyTrendResponse(points=points)


def list_jobs(db: Session, job_type: str | None, status: str | None, limit: int, offset: int) -> JobListResponse:
    filters = []
    if job_type:
        filters.append(ProcessingJob.job_type == job_type)
    if status:
        filters.append(ProcessingJob.status == status)
    total = db.scalar(select(func.count()).select_from(ProcessingJob).where(*filters)) or 0
    q = select(ProcessingJob).where(*filters) if filters else select(ProcessingJob)
    jobs = db.scalars(q.order_by(ProcessingJob.started_at.desc()).offset(offset).limit(limit)).all()
    return JobListResponse(
        items=[JobItem.model_validate(j) for j in jobs],
        total=total,
    )


def list_episodes(
    db: Session,
    source: str | None,
    success: bool | None,
    stage: str | None,
    task: str | None,
    limit: int,
    offset: int,
) -> EpisodeListResponse:
    filters = []
    if source:
        filters.append(Episode.source == source)
    if success is not None:
        filters.append(Episode.success.is_(success))
    if stage:
        filters.append(Episode.stage == stage)
    if task:
        filters.append(Episode.task == task)
    total = db.scalar(select(func.count()).select_from(Episode).where(*filters)) or 0
    q = select(Episode).where(*filters) if filters else select(Episode)
    eps = db.scalars(q.order_by(Episode.collect_date.desc(), Episode.id.desc()).offset(offset).limit(limit)).all()
    return EpisodeListResponse(items=[EpisodeItem.model_validate(e) for e in eps], total=total)


def get_storage(db: Session, history_limit: int = 30) -> StorageResponse:
    latest = db.scalar(select(StorageSnapshot).order_by(StorageSnapshot.snapshot_at.desc()).limit(1))
    history_rows = db.scalars(
        select(StorageSnapshot).order_by(StorageSnapshot.snapshot_at.desc()).limit(history_limit)
    ).all()

    def to_point(s: StorageSnapshot) -> StoragePoint:
        return StoragePoint(
            snapshot_at=s.snapshot_at,
            raw_gb=_bytes_to_gb(s.raw_bytes),
            staging_gb=_bytes_to_gb(s.staging_bytes),
            lerobot_gb=_bytes_to_gb(s.lerobot_bytes),
            training_gb=_bytes_to_gb(s.training_bytes),
        )

    return StorageResponse(
        latest=to_point(latest) if latest else None,
        history=[to_point(s) for s in reversed(history_rows)],
    )
