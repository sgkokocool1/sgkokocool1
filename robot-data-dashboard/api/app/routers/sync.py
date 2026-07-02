from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import RecordJobRequest, StorageResponse, SyncTriggerResponse
from app.services.jobs import record_job
from app.services.sync_manifest import rebuild_daily_stats, snapshot_storage, sync_manifest
from app.models import ProcessingJob

router = APIRouter(tags=["sync"])


@router.get("/storage", response_model=StorageResponse)
def storage(db: Session = Depends(get_db)) -> StorageResponse:
    from app.services.stats import get_storage

    return get_storage(db)


@router.post("/sync/trigger", response_model=SyncTriggerResponse)
def trigger_sync(db: Session = Depends(get_db)) -> SyncTriggerResponse:
    settings = get_settings()
    episodes = sync_manifest(db, settings.data_root)
    rebuild_daily_stats(db)
    snapshot_storage(db, settings.data_root)
    return SyncTriggerResponse(ok=True, message="sync completed", episodes_synced=episodes)


@router.post("/jobs/record", response_model=dict)
def record_job_endpoint(req: RecordJobRequest, db: Session = Depends(get_db)) -> dict:
    job = record_job(db, req)
    return {"id": job.id, "status": job.status.value}
