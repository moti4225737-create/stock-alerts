from collections.abc import Callable
from datetime import datetime


class AutonomousAcquisitionLoop:
    def __init__(
        self,
        coordinator: object,
        clock: Callable[[], datetime],
        waiter: Callable[[int], None],
        tick_seconds: int,
    ) -> None:
        self._coordinator = coordinator
        self._clock = clock
        self._waiter = waiter
        self._tick_seconds = tick_seconds

    def run(self) -> None:
        while True:
            now = self._clock()
            self._coordinator.run_due(now)
            self._waiter(self._tick_seconds)
