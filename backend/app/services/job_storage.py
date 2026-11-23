from app.repositories.job_repository import JobRepository
from app.schemas.job import JobSchema


class JobStorageService:
    """
    Service responsible for storing normalized jobs.

    The service sits between the job aggregator and
    the database repository.
    """

    def __init__(self, repository: JobRepository):
        self.repository = repository

    # ========================================================
    # STORE ONE JOB
    # ========================================================

    def store_job(self, job: JobSchema):
        """
        Store a single normalized job.
        """

        return self.repository.upsert(job)

    # ========================================================
    # STORE MANY JOBS
    # ========================================================

    def store_jobs(
        self,
        jobs: list[JobSchema],
    ):
        """
        Store multiple normalized jobs.
        """

        if not jobs:
            return []

        return self.repository.upsert_many(jobs)

    # ========================================================
    # GET ACTIVE JOBS
    # ========================================================

    def get_active_jobs(
        self,
        limit: int = 100,
        offset: int = 0,
    ):
        """
        Return active jobs from storage.
        """

        return self.repository.get_active(
            limit=limit,
            offset=offset,
        )

    # ========================================================
    # COUNT
    # ========================================================

    def count_active_jobs(self) -> int:
        """
        Return the number of active stored jobs.
        """

        return self.repository.count_active()