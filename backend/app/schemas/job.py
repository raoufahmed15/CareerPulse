from typing import Optional

from pydantic import BaseModel, Field


class JobSchema(BaseModel):
    """
    Unified internal representation of a job.

    Every external job source must be normalized into this schema
    before it is used by the rest of the application.
    """

    title: str
    company: str

    location: Optional[str] = None
    description: Optional[str] = None

    apply_url: str

    source: str
    external_id: Optional[str] = None

    job_type: Optional[str] = None

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None

    remote: Optional[bool] = None

    posted_at: Optional[str] = None

    fingerprint: Optional[str] = None