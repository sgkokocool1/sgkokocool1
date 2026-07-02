from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DistributionResponse, FunnelResponse
from app.services.stats import get_distribution_by_source, get_distribution_by_task, get_funnel

router = APIRouter(tags=["distribution"])


@router.get("/distribution/source", response_model=DistributionResponse)
def distribution_source(db: Session = Depends(get_db)) -> DistributionResponse:
    return get_distribution_by_source(db)


@router.get("/distribution/task", response_model=DistributionResponse)
def distribution_task(db: Session = Depends(get_db)) -> DistributionResponse:
    return get_distribution_by_task(db)


@router.get("/funnel", response_model=FunnelResponse)
def funnel(db: Session = Depends(get_db)) -> FunnelResponse:
    return get_funnel(db)
