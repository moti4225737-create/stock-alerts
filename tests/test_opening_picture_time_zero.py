from datetime import datetime, timezone
from decimal import Decimal

from models.holding_protection_epoch import HoldingProtectionEpochs
from models.portfolio_holding import PortfolioHolding


class MutableClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def __call__(self) -> datetime:
        return self.current


def canonical_identity_for(holding: PortfolioHolding) -> str:
    return f"verified-instrument:{holding.symbol}"


def test_new_holding_receives_one_timezone_aware_time_zero() -> None:
    started_at = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    holding = PortfolioHolding("AAPL", Decimal("1"))
    epochs = HoldingProtectionEpochs(clock=MutableClock(started_at))

    epoch = epochs.establish(canonical_identity_for(holding))

    assert epoch.canonical_instrument_id == canonical_identity_for(holding)
    assert epoch.time_zero == started_at
    assert epoch.time_zero.tzinfo is not None


def test_re_evaluating_same_holding_does_not_move_time_zero() -> None:
    started_at = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    clock = MutableClock(started_at)
    holding = PortfolioHolding("AAPL", Decimal("1"))
    epochs = HoldingProtectionEpochs(clock=clock)

    first = epochs.establish(canonical_identity_for(holding))
    clock.current = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
    replayed = epochs.establish(canonical_identity_for(holding))

    assert replayed == first
    assert replayed.time_zero == started_at


def test_quantity_only_change_preserves_time_zero() -> None:
    started_at = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    clock = MutableClock(started_at)
    original = PortfolioHolding("AAPL", Decimal("1"), average_cost=100.0)
    changed = PortfolioHolding("AAPL", Decimal("2"), average_cost=100.0)
    epochs = HoldingProtectionEpochs(clock=clock)

    first = epochs.establish(canonical_identity_for(original))
    clock.current = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
    after_change = epochs.establish(canonical_identity_for(changed))

    assert after_change == first


def test_average_cost_only_change_preserves_time_zero() -> None:
    started_at = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    clock = MutableClock(started_at)
    original = PortfolioHolding("AAPL", Decimal("1"), average_cost=100.0)
    changed = PortfolioHolding("AAPL", Decimal("1"), average_cost=110.0)
    epochs = HoldingProtectionEpochs(clock=clock)

    first = epochs.establish(canonical_identity_for(original))
    clock.current = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
    after_change = epochs.establish(canonical_identity_for(changed))

    assert after_change == first


def test_restored_epoch_preserves_original_time_zero() -> None:
    started_at = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    holding = PortfolioHolding("AAPL", Decimal("1"))
    original_epochs = HoldingProtectionEpochs(
        clock=MutableClock(started_at),
    )
    original = original_epochs.establish(canonical_identity_for(holding))

    restored_epochs = HoldingProtectionEpochs(
        clock=MutableClock(
            datetime(2026, 8, 26, 9, 0, tzinfo=timezone.utc),
        ),
        restored_epochs=(original,),
    )

    restored = restored_epochs.establish(canonical_identity_for(holding))

    assert restored == original
    assert restored.time_zero == started_at


def test_holding_added_later_receives_its_own_time_zero() -> None:
    first_started_at = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    second_started_at = datetime(2026, 8, 25, 11, 0, tzinfo=timezone.utc)
    clock = MutableClock(first_started_at)
    first_holding = PortfolioHolding("AAPL", Decimal("1"))
    later_holding = PortfolioHolding("MSFT", Decimal("1"))
    epochs = HoldingProtectionEpochs(clock=clock)

    first = epochs.establish(canonical_identity_for(first_holding))
    clock.current = second_started_at
    later = epochs.establish(canonical_identity_for(later_holding))

    assert first.time_zero == first_started_at
    assert later.time_zero == second_started_at
    assert later.time_zero != first.time_zero
