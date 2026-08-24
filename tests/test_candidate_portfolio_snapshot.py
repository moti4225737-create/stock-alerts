from datetime import datetime, timezone
from decimal import Decimal
from importlib import import_module

from models.portfolio_holding import PortfolioHolding


def _snapshot_contract() -> tuple[type, type]:
    module = import_module("models.candidate_portfolio_snapshot")
    return module.CandidatePortfolioSnapshot, module.SnapshotCompleteness


def _holding(symbol: str = "AAPL", quantity: str = "1") -> PortfolioHolding:
    return PortfolioHolding(
        symbol=symbol,
        quantity=Decimal(quantity),
    )


def _source_as_of() -> datetime:
    return datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


def test_complete_candidate_with_positions_is_eligible_for_acceptance() -> None:
    CandidatePortfolioSnapshot, SnapshotCompleteness = _snapshot_contract()

    candidate = CandidatePortfolioSnapshot(
        positions=(_holding(),),
        source_as_of=_source_as_of(),
        completeness=SnapshotCompleteness.COMPLETE,
    )

    assert candidate.is_eligible_for_acceptance is True


def test_complete_empty_candidate_is_eligible_for_acceptance() -> None:
    CandidatePortfolioSnapshot, SnapshotCompleteness = _snapshot_contract()

    candidate = CandidatePortfolioSnapshot(
        positions=(),
        source_as_of=_source_as_of(),
        completeness=SnapshotCompleteness.COMPLETE,
    )

    assert candidate.is_eligible_for_acceptance is True


def test_partial_candidate_is_not_eligible_for_acceptance() -> None:
    CandidatePortfolioSnapshot, SnapshotCompleteness = _snapshot_contract()

    candidate = CandidatePortfolioSnapshot(
        positions=(_holding(),),
        source_as_of=_source_as_of(),
        completeness=SnapshotCompleteness.PARTIAL,
    )

    assert candidate.is_eligible_for_acceptance is False


def test_unknown_candidate_is_not_eligible_for_acceptance() -> None:
    CandidatePortfolioSnapshot, SnapshotCompleteness = _snapshot_contract()

    candidate = CandidatePortfolioSnapshot(
        positions=(_holding(),),
        source_as_of=_source_as_of(),
        completeness=SnapshotCompleteness.UNKNOWN,
    )

    assert candidate.is_eligible_for_acceptance is False


def test_candidate_retains_source_as_of() -> None:
    CandidatePortfolioSnapshot, SnapshotCompleteness = _snapshot_contract()
    source_as_of = _source_as_of()

    candidate = CandidatePortfolioSnapshot(
        positions=(_holding(),),
        source_as_of=source_as_of,
        completeness=SnapshotCompleteness.COMPLETE,
    )

    assert candidate.source_as_of is source_as_of
