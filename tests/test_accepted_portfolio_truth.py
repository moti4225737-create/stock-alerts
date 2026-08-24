from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from models.portfolio_holding import PortfolioHolding


def _contract():
    return import_module(
        "models.accepted_portfolio_truth"
    ).AcceptedPortfolioTruth


def _aware_datetime(hour: int) -> datetime:
    return datetime(2026, 8, 24, hour, 0, tzinfo=timezone.utc)


def test_accepted_truth_retains_exact_positions_and_timestamps() -> None:
    AcceptedPortfolioTruth = _contract()
    position = PortfolioHolding(
        symbol="AAPL",
        quantity=Decimal("7.99"),
    )
    source_as_of = _aware_datetime(12)
    accepted_at = _aware_datetime(13)

    truth = AcceptedPortfolioTruth(
        positions=(position,),
        source_as_of=source_as_of,
        accepted_at=accepted_at,
    )

    assert truth.positions == (position,)
    assert truth.positions[0].quantity == Decimal("7.99")
    assert truth.source_as_of is source_as_of
    assert truth.accepted_at is accepted_at


@pytest.mark.parametrize("naive_field", ["source_as_of", "accepted_at"])
def test_accepted_truth_rejects_naive_timestamps(naive_field) -> None:
    AcceptedPortfolioTruth = _contract()
    timestamps = {
        "source_as_of": _aware_datetime(12),
        "accepted_at": _aware_datetime(13),
    }
    timestamps[naive_field] = datetime(2026, 8, 24, 12, 0)

    with pytest.raises(ValueError, match=naive_field):
        AcceptedPortfolioTruth(positions=(), **timestamps)


def test_empty_accepted_truth_is_a_real_value_not_absence() -> None:
    AcceptedPortfolioTruth = _contract()

    truth = AcceptedPortfolioTruth(
        positions=(),
        source_as_of=_aware_datetime(12),
        accepted_at=_aware_datetime(13),
    )

    assert truth is not None
    assert truth.positions == ()


def test_accepted_truth_contains_only_approved_state_fields() -> None:
    AcceptedPortfolioTruth = _contract()

    assert {field.name for field in fields(AcceptedPortfolioTruth)} == {
        "positions",
        "source_as_of",
        "accepted_at",
    }
