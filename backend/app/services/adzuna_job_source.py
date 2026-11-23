import os
from pathlib import Path
from typing import Any, List

import requests
from dotenv import load_dotenv

from app.schemas.job import JobSchema
from app.services.job_sources import JobSource

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_FILE)


class AdzunaJobSource(JobSource):
    """
    Adzuna implementation of the generic JobSource interface.
    """

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        country: str | None = None,
        base_url: str | None = None,
        timeout: float = 10.0,
    ):
        self.app_id = app_id or os.getenv("ADZUNA_APP_ID")
        self.app_key = app_key or os.getenv("ADZUNA_APP_KEY")
        self.country = country or os.getenv("ADZUNA_COUNTRY", "gb")
        self.base_url = (
            base_url
            or os.getenv(
                "ADZUNA_BASE_URL",
                "https://api.adzuna.com/v1/api",
            )
        ).rstrip("/")

        self.timeout = timeout

        if not self.app_id:
            raise RuntimeError("ADZUNA_APP_ID is not set.")

        if not self.app_key:
            raise RuntimeError("ADZUNA_APP_KEY is not set.")

    @property
    def name(self) -> str:
        return "adzuna"

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

        url = (
            f"{self.base_url}/jobs/"
            f"{self.country}/search/{page}"
        )

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": limit,
            "what": query.strip(),
            "content-type": "application/json",
        }

        if location and location.strip():
            params["where"] = location.strip()

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.Timeout as exc:
            raise RuntimeError(
                "Adzuna request timed out."
            ) from exc

        except requests.HTTPError as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else "unknown"
            )

            raise RuntimeError(
                f"Adzuna API returned HTTP {status_code}."
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Adzuna request failed: {exc}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Adzuna returned invalid JSON."
            ) from exc

        results = payload.get("results", [])

        if not isinstance(results, list):
            raise RuntimeError(
                "Unexpected Adzuna response: "
                "'results' is not a list."
            )

        jobs: List[JobSchema] = []

        for item in results:
            try:
                job = self._normalize_job(item)
                jobs.append(job)

            except Exception:
                # A malformed individual advertisement should not
                # invalidate the complete search response.
                continue

        return jobs

    def _normalize_job(self, item: dict[str, Any]) -> JobSchema:
        company = item.get("company") or {}
        location = item.get("location") or {}

        company_name = (
            company.get("display_name")
            if isinstance(company, dict)
            else None
        )

        location_name = (
            location.get("display_name")
            if isinstance(location, dict)
            else None
        )

        title = item.get("title")
        apply_url = item.get("redirect_url")

        if not title:
            raise ValueError("Adzuna job has no title.")

        if not company_name:
            company_name = "Unknown company"

        if not apply_url:
            raise ValueError(
                f"Adzuna job '{title}' has no apply URL."
            )

        contract_time = item.get("contract_time")
        contract_type = item.get("contract_type")

        job_type = self._build_job_type(
            contract_time=contract_time,
            contract_type=contract_type,
        )

        return JobSchema(
            title=str(title).strip(),
            company=str(company_name).strip(),
            location=location_name,
            description=item.get("description"),
            apply_url=str(apply_url),
            source=self.name,
            external_id=str(item["id"])
            if item.get("id") is not None
            else None,
            job_type=job_type,
            salary_min=self._to_float(item.get("salary_min")),
            salary_max=self._to_float(item.get("salary_max")),
            salary_currency=None,
            remote=None,
            posted_at=item.get("created"),
        )

    @staticmethod
    def _build_job_type(
        contract_time: str | None,
        contract_type: str | None,
    ) -> str | None:

        values = [
            value
            for value in (contract_time, contract_type)
            if value
        ]

        if not values:
            return None

        return ", ".join(values)

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None