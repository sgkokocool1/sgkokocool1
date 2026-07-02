from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EpisodeMetrics(BaseModel):
    total: int = 0
    success: int = 0
    failed: int = 0
    success_rate: float = 0.0
    imported: int = 0
    pending: int = 0
    frames_total: int = 0


class SourceBreakdown(BaseModel):
    total: int = 0
    success: int = 0
    failed: int = 0
    imported: int = 0
    frames: int = 0


class JobsSummary(BaseModel):
    total: int = 0
    success: int = 0
    failed: int = 0


class StorageSummary(BaseModel):
    raw_gb: float = 0.0
    staging_gb: float = 0.0
    lerobot_gb: float = 0.0
    training_gb: float = 0.0


class OverviewResponse(BaseModel):
    episodes: EpisodeMetrics
    by_source: dict[str, SourceBreakdown]
    jobs_7d: JobsSummary
    storage: StorageSummary
    updated_at: datetime


class FunnelStage(BaseModel):
    name: str
    label: str
    count: int


class FunnelResponse(BaseModel):
    stages: list[FunnelStage]


class DistributionItem(BaseModel):
    key: str
    total: int
    success: int
    failed: int
    imported: int
    frames: int


class DistributionResponse(BaseModel):
    items: list[DistributionItem]


class DailyTrendPoint(BaseModel):
    date: date
    total: int
    success: int
    failed: int
    imported: int


class DailyTrendResponse(BaseModel):
    points: list[DailyTrendPoint]


class JobItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_sec: float | None
    triggered_by: str
    episodes_in: int
    episodes_ok: int
    episodes_fail: int
    frames_in: int
    error_message: str | None = None


class JobListResponse(BaseModel):
    items: list[JobItem]
    total: int


class EpisodeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path: str
    collect_date: date
    session_key: str
    episode_name: str
    source: str
    task: str
    success: bool
    fps: int
    frames: int
    stage: str
    imported_to: str | None
    operator: str | None
    validation_ok: bool | None


class EpisodeListResponse(BaseModel):
    items: list[EpisodeItem]
    total: int


class DatasetItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: str
    root_path: str
    total_episodes: int | None
    total_frames: int | None
    total_tasks: int | None
    fps: int | None
    robot_type: str | None
    built_at: datetime | None


class DatasetListResponse(BaseModel):
    items: list[DatasetItem]


class StoragePoint(BaseModel):
    snapshot_at: datetime
    raw_gb: float
    staging_gb: float
    lerobot_gb: float
    training_gb: float


class StorageResponse(BaseModel):
    latest: StoragePoint | None
    history: list[StoragePoint]


class SyncTriggerResponse(BaseModel):
    ok: bool
    message: str
    episodes_synced: int = 0


class RecordJobRequest(BaseModel):
    job_type: str
    status: str = "success"
    triggered_by: str = "manual"
    params_json: dict[str, Any] | None = None
    report_json: dict[str, Any] | None = None
    log_path: str | None = None
    error_message: str | None = None
    episodes_in: int = 0
    episodes_ok: int = 0
    episodes_fail: int = 0
    frames_in: int = 0
    duration_sec: float | None = None
    episode_paths: list[str] = Field(default_factory=list)
