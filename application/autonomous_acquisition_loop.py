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

    def run(self, max_cycles: int | None = None) -> None:
        cycles = 0

        while max_cycles is None or cycles < max_cycles:
            now = self._clock()
            self._coordinator.run_due(now)
            cycles += 1

            if max_cycles is not None and cycles >= max_cycles:
                return

            self._waiter(self._tick_seconds)
