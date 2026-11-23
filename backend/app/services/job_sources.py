from abc import ABC, abstractmethod
from typing import List

from app.schemas.job import JobSchema


class JobSource(ABC):
    """
    Abstract interface for all job providers.

    Every external job source must implement this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique source name."""
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query: str,
        location: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> List[JobSchema]:
        """
        Search for jobs and return normalized JobSchema objects.
        """
        raise NotImplementedError