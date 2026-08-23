from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable


@dataclass(frozen=True)
class HealthchecksEvidence:
    health_passed: bool | None
    last_ping: str | None
    error: str | None = None


class HealthchecksEvidenceCollector:
    def __init__(
        self,
        *,
        check_name: str,
        requester: Callable[..., Any],
        api_key: str | None = None,
    ) -> None:
        self._check_name = check_name
        self._requester = requester
        self._api_key = api_key

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    def collect(
        self,
        *,
        deployed_at: str | None = None,
    ) -> HealthchecksEvidence:
        request_kwargs: dict[str, Any] = {
            "timeout": 10,
        }

        if self._api_key is not None:
            request_kwargs["headers"] = {
                "Accept": "application/json",
                "User-Agent": "Stock-Sentinel-Gate-Evidence",
                "X-Api-Key": self._api_key,
            }

        try:
            response = self._requester(
                "https://healthchecks.io/api/v3/checks/",
                **request_kwargs,
            )
            response.raise_for_status()

            payload = response.json()
        except Exception:
            return HealthchecksEvidence(
                health_passed=None,
                last_ping=None,
                error="healthchecks_api_error",
            )

        checks = payload.get(
            "checks",
            [],
        )

        matching_check = next(
            (
                check
                for check in checks
                if check.get("name") == self._check_name
            ),
            None,
        )

        if matching_check is None:
            return HealthchecksEvidence(
                health_passed=None,
                last_ping=None,
            )

        status = matching_check.get("status")
        last_ping = matching_check.get("last_ping")

        if status != "up":
            health_passed = False
        elif deployed_at is None:
            health_passed = True
        elif last_ping is None:
            health_passed = None
        else:
            health_passed = (
                self._parse_timestamp(last_ping)
                > self._parse_timestamp(deployed_at)
            )

        return HealthchecksEvidence(
            health_passed=health_passed,
            last_ping=last_ping,
        )
