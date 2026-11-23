from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Job(Base):
    """
    Database model for a normalized job.

    This model stores the current/cached representation of a job
    collected from external job providers.

    Important:
    - This is STORAGE only.
    - Search Intent is NOT stored here.
    - Match Score is NOT stored here.
    """

    __tablename__ = "jobs"

    # ---------------------------------------------------------
    # Primary Key
    # ---------------------------------------------------------

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # ---------------------------------------------------------
    # Core Job Identity
    # ---------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------

    apply_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ---------------------------------------------------------
    # Source Information
    # ---------------------------------------------------------

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ---------------------------------------------------------
    # Job Details
    # ---------------------------------------------------------

    job_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    salary_min: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    salary_max: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    salary_currency: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    remote: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Source Publication
    # ---------------------------------------------------------

    posted_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ---------------------------------------------------------
    # Deduplication
    # ---------------------------------------------------------

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # ---------------------------------------------------------
    # Freshness / Storage Lifecycle
    # ---------------------------------------------------------

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # ---------------------------------------------------------
    # Database Constraints / Indexes
    # ---------------------------------------------------------

    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_id",
            name="uq_jobs_source_external_id",
        ),
        Index(
            "ix_jobs_source",
            "source",
        ),
        Index(
            "ix_jobs_posted_at",
            "posted_at",
        ),
        Index(
            "ix_jobs_last_seen_at",
            "last_seen_at",
        ),
    )

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Job("
            f"id={self.id}, "
            f"title={self.title!r}, "
            f"company={self.company!r}, "
            f"source={self.source!r}"
            f")>"
        )