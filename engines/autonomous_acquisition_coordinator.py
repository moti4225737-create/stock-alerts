from collections.abc import Callable
from datetime import datetime, timedelta

from engines.source_acquisition_policy import SourceAcquisitionPolicy


class AutonomousAcquisitionCoordinator:
    _INITIAL_BACKOFF_SECONDS = 60
    _MAX_BACKOFF_SECONDS = 900

    def __init__(
        self,
        sources: dict[str, Callable[[], None]],
        policies: dict[str, SourceAcquisitionPolicy],
    ) -> None:
        self._sources = sources
        self._policies = policies
        self._last_run: dict[str, datetime] = {}
        self._failure_counts: dict[str, int] = {}
        self._retry_not_before: dict[str, datetime] = {}

    def run_due(self, now: datetime) -> None:
        for source_name, runner in self._sources.items():
            retry_not_before = self._retry_not_before.get(
                source_name
            )

            if (
                retry_not_before is not None
                and now < retry_not_before
            ):
                continue

            policy = self._policies[source_name]
            last_run = self._last_run.get(source_name)

            if last_run is not None:
                interval_seconds = policy.interval_at_datetime(now)

                interval = timedelta(
                    seconds=interval_seconds,
                )

                if now - last_run < interval:
                    continue

            try:
                runner()
            except Exception as error:
                failure_count = (
                    self._failure_counts.get(source_name, 0) + 1
                )
                self._failure_counts[source_name] = failure_count

                backoff_seconds = min(
                    self._INITIAL_BACKOFF_SECONDS
                    * (2 ** (failure_count - 1)),
                    self._MAX_BACKOFF_SECONDS,
                )

                self._retry_not_before[source_name] = (
                    now
                    + timedelta(seconds=backoff_seconds)
                )

                print(
                    f"[WARNING] Autonomous source "
                    f"{source_name} failed: {error}. "
                    f"Retry in {backoff_seconds} seconds."
                )
                continue

            self._failure_counts.pop(source_name, None)
            self._retry_not_before.pop(source_name, None)
            self._last_run[source_name] = now
