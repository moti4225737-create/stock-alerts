from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from application.autonomous_acquisition_loop import (
    AutonomousAcquisitionLoop,
)


def test_autonomous_acquisition_loop_checks_coordinator_each_tick() -> None:
    coordinator = Mock()

    times = iter(
        [
            datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 7, 12, 0, 1, tzinfo=timezone.utc),
        ]
    )

    clock = Mock(side_effect=lambda: next(times))
    waiter = Mock(side_effect=[None, KeyboardInterrupt])

    loop = AutonomousAcquisitionLoop(
        coordinator=coordinator,
        clock=clock,
        waiter=waiter,
        tick_seconds=1,
    )

    with pytest.raises(KeyboardInterrupt):
        loop.run()

    assert coordinator.run_due.call_count == 2
    assert coordinator.run_due.call_args_list[0].args[0] == datetime(
        2026,
        8,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )
    assert coordinator.run_due.call_args_list[1].args[0] == datetime(
        2026,
        8,
        7,
        12,
        0,
        1,
        tzinfo=timezone.utc,
    )
    assert waiter.call_count == 2
    waiter.assert_called_with(1)
