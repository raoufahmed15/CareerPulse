import hashlib
import re

from app.schemas.job import JobSchema


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)

    return value


def generate_job_fingerprint(job: JobSchema) -> str:
    """
    Generate a stable fingerprint for a job.

    The fingerprint intentionally uses normalized job identity
    fields rather than source-specific fields.
    """

    title = _normalize_text(job.title)
    company = _normalize_text(job.company)
    location = _normalize_text(job.location)

    identity = "|".join(
        [
            title,
            company,
            location,
        ]
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


def assign_fingerprint(job: JobSchema) -> JobSchema:
    """
    Return a copy of the job with its fingerprint assigned.
    """

    fingerprint = generate_job_fingerprint(job)

    return job.model_copy(
        update={"fingerprint": fingerprint}
    )


def deduplicate_jobs(jobs: list[JobSchema]) -> list[JobSchema]:
    """
    Remove duplicate jobs using their fingerprint.

    The first occurrence is preserved.
    """

    seen: set[str] = set()
    unique_jobs: list[JobSchema] = []

    for job in jobs:
        fingerprint = (
            job.fingerprint
            or generate_job_fingerprint(job)
        )

        if fingerprint in seen:
            continue

        seen.add(fingerprint)

        if job.fingerprint != fingerprint:
            job = job.model_copy(
                update={"fingerprint": fingerprint}
            )

        unique_jobs.append(job)

    return unique_jobs