from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Episode, JobEpAction, JobEpisode, JobStatus, JobType, ProcessingJob
from app.schemas import RecordJobRequest


def record_job(db: Session, req: RecordJobRequest) -> ProcessingJob:
    now = datetime.now(timezone.utc)
    job = ProcessingJob(
        job_type=JobType(req.job_type),
        status=JobStatus(req.status),
        started_at=now,
        finished_at=now if req.status != "running" else None,
        duration_sec=req.duration_sec,
        triggered_by=req.triggered_by,
        params_json=req.params_json,
        report_json=req.report_json,
        log_path=req.log_path,
        error_message=req.error_message,
        episodes_in=req.episodes_in,
        episodes_ok=req.episodes_ok,
        episodes_fail=req.episodes_fail,
        frames_in=req.frames_in,
    )
    db.add(job)
    db.flush()

    if req.episode_paths:
        eps = db.scalars(select(Episode).where(Episode.path.in_(req.episode_paths))).all()
        ep_map = {e.path: e for e in eps}
        for path in req.episode_paths:
            ep = ep_map.get(path)
            if not ep:
                continue
            action = JobEpAction.import_ if req.status == "success" else JobEpAction.fail
            db.add(JobEpisode(job_id=job.id, episode_id=ep.id, action=action))

    db.commit()
    db.refresh(job)
    return job
