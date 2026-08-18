from collections.abc import Callable
from datetime import datetime
from typing import Any


class HealthchecksWorkEvidenceReporter:
    def __init__(
        self,
        ping_url: str,
        requester: Callable[..., Any],
        timeout_seconds: int = 2,
    ) -> None:
        self._ping_url = ping_url
        self._requester = requester
        self._timeout_seconds = timeout_seconds

    def __call__(
        self,
        source_name: str,
        completed_at: datetime,
    ) -> None:
        response = self._requester(
            self._ping_url,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
