from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobSchema


class JobRepository:
    """
    Database repository for Job persistence.

    Responsibilities:
    - Save new jobs
    - Update existing jobs
    - Find jobs by fingerprint
    - Find jobs by source/external_id
    - Read active jobs
    - Mark jobs inactive

    This class does NOT perform:
    - Search Intent
    - Resume Matching
    - Match Score
    - Job Ranking
    """

    def __init__(self, db: Session):
        self.db = db

    # ========================================================
    # CREATE / UPDATE
    # ========================================================

    def upsert(self, job: JobSchema) -> Job:
        """
        Insert a new job or update an existing job.

        Fingerprint is the primary deduplication key.
        """

        if not job.fingerprint:
            raise ValueError(
                "Job fingerprint is required before storage."
            )

        existing = self.get_by_fingerprint(
            job.fingerprint
        )

        if existing:
            self._update_model(existing, job)

            existing.last_seen_at = datetime.now(timezone.utc)
            existing.updated_at = datetime.now(timezone.utc)
            existing.is_active = True

            self.db.commit()
            self.db.refresh(existing)

            return existing

        db_job = self._schema_to_model(job)

        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)

        return db_job

    def upsert_many(
        self,
        jobs: list[JobSchema],
    ) -> list[Job]:
        """
        Insert or update multiple jobs in one transaction.
        """

        stored_jobs: list[Job] = []

        try:
            for job in jobs:
                if not job.fingerprint:
                    raise ValueError(
                        "Every job must have a fingerprint."
                    )

                existing = self.get_by_fingerprint(
                    job.fingerprint
                )

                if existing:
                    self._update_model(existing, job)

                    existing.last_seen_at = (
                        datetime.now(timezone.utc)
                    )
                    existing.updated_at = (
                        datetime.now(timezone.utc)
                    )
                    existing.is_active = True

                    stored_jobs.append(existing)

                else:
                    db_job = self._schema_to_model(job)

                    self.db.add(db_job)
                    stored_jobs.append(db_job)

            self.db.commit()

            for job in stored_jobs:
                self.db.refresh(job)

            return stored_jobs

        except Exception:
            self.db.rollback()
            raise

    # ========================================================
    # READ
    # ========================================================

    def get_by_id(
        self,
        job_id: int,
    ) -> Job | None:
        """
        Get a job by internal database ID.
        """

        statement = select(Job).where(
            Job.id == job_id
        )

        return self.db.scalar(statement)

    def get_by_fingerprint(
        self,
        fingerprint: str,
    ) -> Job | None:
        """
        Get a job by its stable fingerprint.
        """

        statement = select(Job).where(
            Job.fingerprint == fingerprint
        )

        return self.db.scalar(statement)

    def get_by_source_external_id(
        self,
        source: str,
        external_id: str,
    ) -> Job | None:
        """
        Get a job using the provider source and
        its external job identifier.
        """

        statement = select(Job).where(
            Job.source == source,
            Job.external_id == external_id,
        )

        return self.db.scalar(statement)

    def get_active(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """
        Return active jobs with pagination.
        """

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        if offset < 0:
            raise ValueError(
                "offset cannot be negative."
            )

        statement = (
            select(Job)
            .where(Job.is_active.is_(True))
            .order_by(Job.last_seen_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_active(self) -> int:
        """
        Return the number of active jobs.
        """

        from sqlalchemy import func

        statement = select(
            func.count(Job.id)
        ).where(
            Job.is_active.is_(True)
        )

        return self.db.scalar(statement) or 0

    # ========================================================
    # FRESHNESS
    # ========================================================

    def mark_inactive(
        self,
        job: Job,
    ) -> Job:
        """
        Mark a job as inactive.

        The record is kept in the database so historical
        storage is not destroyed.
        """

        job.is_active = False
        job.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)

        return job

    # ========================================================
    # CONVERSION
    # ========================================================

    @staticmethod
    def _schema_to_model(
        job: JobSchema,
    ) -> Job:
        """
        Convert JobSchema into SQLAlchemy Job model.
        """

        now = datetime.now(timezone.utc)

        return Job(
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            apply_url=job.apply_url,
            source=job.source,
            external_id=job.external_id,
            job_type=job.job_type,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            remote=job.remote,
            posted_at=job.posted_at,
            fingerprint=job.fingerprint,
            first_seen_at=now,
            last_seen_at=now,
            updated_at=now,
            is_active=True,
        )

    @staticmethod
    def _update_model(
        db_job: Job,
        job: JobSchema,
    ) -> None:
        """
        Update the stored job with the latest normalized data.
        """

        db_job.title = job.title
        db_job.company = job.company
        db_job.location = job.location
        db_job.description = job.description
        db_job.apply_url = job.apply_url
        db_job.source = job.source
        db_job.external_id = job.external_id
        db_job.job_type = job.job_type
        db_job.salary_min = job.salary_min
        db_job.salary_max = job.salary_max
        db_job.salary_currency = job.salary_currency
        db_job.remote = job.remote
        db_job.posted_at = job.posted_at
        db_job.fingerprint = job.fingerprint