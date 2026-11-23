from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.repositories.job_repository import JobRepository
from app.services.adzuna_job_source import AdzunaJobSource
from app.services.job_aggregator import JobAggregator
from app.services.job_storage import JobStorageService
from app.services.remotive_job_source import RemotiveJobSource


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


def get_job_aggregator(
    db: Session = Depends(get_db),
) -> JobAggregator:
    repository = JobRepository(db)
    storage = JobStorageService(repository)
    return JobAggregator(
        sources=[
            AdzunaJobSource(),
            RemotiveJobSource(),
        ],
        storage=storage,
    )


@router.get("/search")
def search_jobs(
    q: str = Query(..., min_length=1),
    location: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    aggregator: JobAggregator = Depends(get_job_aggregator),
):
    try:
        jobs = aggregator.search(
            query=q,
            location=location,
            page=page,
            limit=limit,
        )

        return {
            "query": q,
            "location": location,
            "page": page,
            "limit": limit,
            "count": len(jobs),
            "jobs": [
                job.model_dump()
                for job in jobs
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Job search failed: {str(exc)}",
        )