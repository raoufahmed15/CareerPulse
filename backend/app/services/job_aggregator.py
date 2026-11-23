from typing import List

from app.schemas.job import JobSchema
from app.services.job_sources import JobSource
from app.services.job_deduplication import (
    assign_fingerprint,
    deduplicate_jobs,
)
from app.services.job_storage import JobStorageService


class JobAggregator:
    """
    Aggregates jobs from multiple external sources.

    Flow:
    1. Search all configured sources.
    2. Normalize results into JobSchema.
    3. Assign fingerprints.
    4. Remove duplicate jobs.
    5. Store normalized jobs in PostgreSQL.
    6. Return only the requested final number of jobs.
    """

    def __init__(
        self,
        sources: List[JobSource],
        storage: JobStorageService | None = None,
    ):
        self.sources = sources
        self.storage = storage

    def search(
        self,
        query: str,
        location: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> List[JobSchema]:

        if not query or not query.strip():
            raise ValueError(
                "Job search query cannot be empty."
            )

        if page < 1:
            raise ValueError("Page must be >= 1.")

        if limit < 1:
            raise ValueError("Limit must be >= 1.")

        limit = min(limit, 50)

        all_jobs: List[JobSchema] = []

        # ========================================================
        # 1. SEARCH ALL SOURCES
        # ========================================================

        for source in self.sources:
            try:
                jobs = source.search(
                    query=query,
                    location=location,
                    page=page,
                    limit=limit,
                )

                if not jobs:
                    continue

                all_jobs.extend(jobs)

            except Exception:
                # One provider failing must not break
                # the complete aggregation process.
                continue

        # ========================================================
        # 2. ASSIGN FINGERPRINT
        # ========================================================

        fingerprinted_jobs: List[JobSchema] = []

        for job in all_jobs:
            try:
                fingerprinted_job = assign_fingerprint(job)
                fingerprinted_jobs.append(
                    fingerprinted_job
                )

            except Exception:
                continue

        # ========================================================
        # 3. DEDUPLICATE
        # ========================================================

        unique_jobs = deduplicate_jobs(
            fingerprinted_jobs
        )

        # ========================================================
        # 4. STORE IN POSTGRESQL
        # ========================================================

        if self.storage and unique_jobs:
            self.storage.store_jobs(unique_jobs)

        # ========================================================
        # 5. RETURN FINAL RESULT
        # ========================================================

        return unique_jobs[:limit]