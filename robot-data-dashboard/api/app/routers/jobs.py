from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DailyTrendResponse, JobListResponse
from app.services.stats import get_daily_trend, list_jobs

router = APIRouter(tags=["jobs"])


@router.get("/trend/daily", response_model=DailyTrendResponse)
def daily_trend(
    db: Session = Depends(get_db),
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> DailyTrendResponse:
    return get_daily_trend(db, date_from, date_to)


@router.get("/jobs", response_model=JobListResponse)
def jobs(
    db: Session = Depends(get_db),
    job_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> JobListResponse:
    return list_jobs(db, job_type, status, limit, offset)
