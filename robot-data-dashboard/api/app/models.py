import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class EpisodeStage(str, enum.Enum):
    staging = "staging"
    raw_archived = "raw_archived"
    validation_failed = "validation_failed"
    pending_import = "pending_import"
    imported = "imported"
    skipped = "skipped"


class JobType(str, enum.Enum):
    daily_ingest = "daily_ingest"
    build_weekly = "build_weekly"
    build_subset = "build_subset"
    build_create = "build_create"
    build_resume = "build_resume"
    train = "train"
    weekly_qc = "weekly_qc"


class JobStatus(str, enum.Enum):
    running = "running"
    success = "success"
    failed = "failed"
    partial = "partial"


class JobEpAction(str, enum.Enum):
    ingest = "ingest"
    import_ = "import"
    skip = "skip"
    fail = "fail"


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("collect_date", "session_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_key: Mapped[str] = mapped_column(String(128), nullable=False)
    collect_date: Mapped[date] = mapped_column(Date, nullable=False)
    operator: Mapped[str | None] = mapped_column(String(64))
    robot_id: Mapped[str | None] = mapped_column(String(64))
    environment: Mapped[str | None] = mapped_column(String(128))
    source: Mapped[str | None] = mapped_column(String(32))
    schema_version: Mapped[str] = mapped_column(String(16), default="v1")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    collect_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    session_key: Mapped[str] = mapped_column(String(128), nullable=False)
    episode_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    task: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    fps: Mapped[int] = mapped_column(Integer, nullable=False)
    frames: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_sec: Mapped[float | None] = mapped_column(Float)
    operator: Mapped[str | None] = mapped_column(String(64))
    robot_id: Mapped[str | None] = mapped_column(String(64))
    stage: Mapped[EpisodeStage] = mapped_column(
        Enum(EpisodeStage, name="episode_stage", values_callable=lambda x: [e.value for e in x]),
        default=EpisodeStage.raw_archived,
        index=True,
    )
    imported_to: Mapped[str | None] = mapped_column(String(256), index=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    validation_ok: Mapped[bool | None] = mapped_column(Boolean)
    validation_errors: Mapped[dict | None] = mapped_column(JSONB)
    disk_bytes: Mapped[int | None] = mapped_column(BigInteger)
    meta_json: Mapped[dict | None] = mapped_column(JSONB)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    root_path: Mapped[str] = mapped_column(String(512), nullable=False)
    total_episodes: Mapped[int | None] = mapped_column(Integer)
    total_frames: Mapped[int | None] = mapped_column(Integer)
    total_tasks: Mapped[int | None] = mapped_column(Integer)
    fps: Mapped[int | None] = mapped_column(Integer)
    robot_type: Mapped[str | None] = mapped_column(String(64))
    codebase_version: Mapped[str | None] = mapped_column(String(16))
    info_json: Mapped[dict | None] = mapped_column(JSONB)
    built_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.running,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_sec: Mapped[float | None] = mapped_column(Float)
    triggered_by: Mapped[str] = mapped_column(String(64), default="cron")
    params_json: Mapped[dict | None] = mapped_column(JSONB)
    report_json: Mapped[dict | None] = mapped_column(JSONB)
    log_path: Mapped[str | None] = mapped_column(String(512))
    error_message: Mapped[str | None] = mapped_column(Text)
    episodes_in: Mapped[int] = mapped_column(Integer, default=0)
    episodes_ok: Mapped[int] = mapped_column(Integer, default=0)
    episodes_fail: Mapped[int] = mapped_column(Integer, default=0)
    frames_in: Mapped[int] = mapped_column(Integer, default=0)

    episode_links: Mapped[list["JobEpisode"]] = relationship(back_populates="job")


class JobEpisode(Base):
    __tablename__ = "job_episodes"

    job_id: Mapped[int] = mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), primary_key=True)
    action: Mapped[JobEpAction] = mapped_column(
        Enum(JobEpAction, name="job_ep_action", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(Text)

    job: Mapped[ProcessingJob] = relationship(back_populates="episode_links")


class DailyStat(Base):
    __tablename__ = "daily_stats"
    __table_args__ = (UniqueConstraint("stat_date", "source", "task"),)

    stat_date: Mapped[date] = mapped_column(Date, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), primary_key=True, default="_all")
    task: Mapped[str] = mapped_column(String(256), primary_key=True, default="_all")
    episodes_total: Mapped[int] = mapped_column(Integer, default=0)
    episodes_success: Mapped[int] = mapped_column(Integer, default=0)
    episodes_failed: Mapped[int] = mapped_column(Integer, default=0)
    frames_total: Mapped[int] = mapped_column(BigInteger, default=0)
    episodes_imported: Mapped[int] = mapped_column(Integer, default=0)
    episodes_pending: Mapped[int] = mapped_column(Integer, default=0)
    jobs_total: Mapped[int] = mapped_column(Integer, default=0)
    jobs_success: Mapped[int] = mapped_column(Integer, default=0)
    jobs_failed: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StorageSnapshot(Base):
    __tablename__ = "storage_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    raw_bytes: Mapped[int | None] = mapped_column(BigInteger)
    staging_bytes: Mapped[int | None] = mapped_column(BigInteger)
    lerobot_bytes: Mapped[int | None] = mapped_column(BigInteger)
    training_bytes: Mapped[int | None] = mapped_column(BigInteger)
    builds_bytes: Mapped[int | None] = mapped_column(BigInteger)
    details_json: Mapped[dict | None] = mapped_column(JSONB)
