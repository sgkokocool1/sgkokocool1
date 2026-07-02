from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dataset
from app.schemas import DatasetItem, DatasetListResponse, EpisodeListResponse
from app.services.stats import list_episodes

router = APIRouter(tags=["episodes"])


@router.get("/episodes", response_model=EpisodeListResponse)
def episodes(
    db: Session = Depends(get_db),
    source: Annotated[str | None, Query()] = None,
    success: Annotated[bool | None, Query()] = None,
    stage: Annotated[str | None, Query()] = None,
    task: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EpisodeListResponse:
    return list_episodes(db, source, success, stage, task, limit, offset)


@router.get("/datasets", response_model=DatasetListResponse)
def datasets(db: Session = Depends(get_db)) -> DatasetListResponse:
    rows = db.scalars(select(Dataset).order_by(Dataset.updated_at.desc())).all()
    return DatasetListResponse(items=[DatasetItem.model_validate(d) for d in rows])
