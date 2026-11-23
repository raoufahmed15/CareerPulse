from typing import Any, List

import requests

from app.schemas.job import JobSchema
from app.services.job_sources import JobSource


class RemotiveJobSource(JobSource):
    """
    Remotive implementation of the generic JobSource interface.
    """

    API_URL = "https://remotive.com/api/remote-jobs"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "remotive"

    def search(
        self,
        query: str,
        location: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> List[JobSchema]:

        if not query or not query.strip():
            raise ValueError("Job search query cannot be empty.")

        if page < 1:
            raise ValueError("Page must be >= 1.")

        if limit < 1:
            raise ValueError("Limit must be >= 1.")

        limit = min(limit, 50)

        params = {
            "search": query.strip(),
        }

        try:
            response = requests.get(
                self.API_URL,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.Timeout as exc:
            raise RuntimeError(
                "Remotive request timed out."
            ) from exc

        except requests.HTTPError as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else "unknown"
            )

            raise RuntimeError(
                f"Remotive API returned HTTP {status_code}."
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Remotive request failed: {exc}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Remotive returned invalid JSON."
            ) from exc

        results = payload.get("jobs", [])

        if not isinstance(results, list):
            raise RuntimeError(
                "Unexpected Remotive response: "
                "'jobs' is not a list."
            )

        jobs: List[JobSchema] = []

        for item in results[:limit]:
            try:
                jobs.append(self._normalize_job(item))
            except Exception:
                continue

        return jobs

    def _normalize_job(self, item: dict[str, Any]) -> JobSchema:
        title = item.get("title")
        company = item.get("company_name")
        apply_url = item.get("url")

        if not title:
            raise ValueError("Remotive job has no title.")

        if not company:
            company = "Unknown company"

        if not apply_url:
            raise ValueError(
                f"Remotive job '{title}' has no apply URL."
            )

        salary = item.get("salary")
        salary_min = None
        salary_max = None

        if isinstance(salary, str):
            # Remotive salary is often free-form text,
            # so we keep it out of numeric salary fields.
            pass

        return JobSchema(
            title=str(title).strip(),
            company=str(company).strip(),
            location=item.get("candidate_required_location"),
            description=item.get("description"),
            apply_url=str(apply_url),
            source=self.name,
            external_id=(
                str(item["id"])
                if item.get("id") is not None
                else None
            ),
            job_type=item.get("job_type"),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=None,
            remote=True,
            posted_at=item.get("publication_date"),
        )