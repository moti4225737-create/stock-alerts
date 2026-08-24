from datetime import datetime, timezone
from decimal import Decimal
from importlib import import_module

from models.portfolio_holding import PortfolioHolding


def _contracts() -> tuple[type, type, type, type]:
    snapshot_module = import_module("models.candidate_portfolio_snapshot")
    reconciliation_module = import_module(
        "application.portfolio_truth_reconciler"
    )
    return (
        snapshot_module.CandidatePortfolioSnapshot,
        snapshot_module.SnapshotCompleteness,
        reconciliation_module.PortfolioAcquisitionResult,
        reconciliation_module.PortfolioTruthReconciler,
    )


def _holding(symbol: str, quantity: str) -> PortfolioHolding:
    return PortfolioHolding(
        symbol=symbol,
        quantity=Decimal(quantity),
    )


def _candidate(
    positions: tuple[PortfolioHolding, ...],
    completeness_name: str = "COMPLETE",
):
    (
        CandidatePortfolioSnapshot,
        SnapshotCompleteness,
        _,
        _,
    ) = _contracts()
    return CandidatePortfolioSnapshot(
        positions=positions,
        source_as_of=datetime(
            2026,
            8,
            24,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        completeness=getattr(SnapshotCompleteness, completeness_name),
    )


def _success(candidate):
    _, _, PortfolioAcquisitionResult, _ = _contracts()
    return PortfolioAcquisitionResult.succeeded(candidate)


def _reconciler():
    _, _, _, PortfolioTruthReconciler = _contracts()
    return PortfolioTruthReconciler()


def test_first_complete_candidate_becomes_authoritative_truth() -> None:
    reconciler = _reconciler()

    reconciler.apply(
        _success(_candidate((_holding("AAPL", "7.99"),)))
    )

    assert reconciler.portfolio.holdings == [
        _holding("AAPL", "7.99")
    ]


def test_later_complete_candidate_replaces_prior_truth() -> None:
    reconciler = _reconciler()
    reconciler.apply(_success(_candidate((_holding("AAPL", "10"),))))

    reconciler.apply(_success(_candidate((_holding("MSFT", "4"),))))

    assert reconciler.portfolio.holdings == [_holding("MSFT", "4")]


def test_failed_acquisition_does_not_erase_prior_truth() -> None:
    _, _, PortfolioAcquisitionResult, _ = _contracts()
    reconciler = _reconciler()
    original = _holding("AAPL", "10")
    reconciler.apply(_success(_candidate((original,))))

    reconciler.apply(PortfolioAcquisitionResult.failed())

    assert reconciler.portfolio.holdings == [original]


def test_partial_candidate_does_not_replace_prior_truth() -> None:
    reconciler = _reconciler()
    original = _holding("AAPL", "10")
    reconciler.apply(_success(_candidate((original,))))

    reconciler.apply(
        _success(
            _candidate(
                (_holding("MSFT", "2"),),
                completeness_name="PARTIAL",
            )
        )
    )

    assert reconciler.portfolio.holdings == [original]


def test_unknown_candidate_does_not_replace_prior_truth() -> None:
    reconciler = _reconciler()
    original = _holding("AAPL", "10")
    reconciler.apply(_success(_candidate((original,))))

    reconciler.apply(
        _success(
            _candidate(
                (_holding("MSFT", "2"),),
                completeness_name="UNKNOWN",
            )
        )
    )

    assert reconciler.portfolio.holdings == [original]


def test_complete_empty_candidate_replaces_truth_with_empty_portfolio() -> None:
    reconciler = _reconciler()
    reconciler.apply(
        _success(_candidate((_holding("AAPL", "10"),)))
    )

    reconciler.apply(_success(_candidate(())))

    assert reconciler.portfolio.holdings == []


def test_complete_candidate_reflects_position_reduction() -> None:
    reconciler = _reconciler()
    reconciler.apply(
        _success(_candidate((_holding("AAPL", "10"),)))
    )

    reconciler.apply(
        _success(_candidate((_holding("AAPL", "7.99"),)))
    )

    assert reconciler.portfolio.get("AAPL").quantity == Decimal("7.99")


def test_complete_candidate_removes_fully_closed_position() -> None:
    reconciler = _reconciler()
    reconciler.apply(
        _success(
            _candidate(
                (
                    _holding("AAPL", "10"),
                    _holding("MSFT", "3"),
                )
            )
        )
    )

    reconciler.apply(_success(_candidate((_holding("MSFT", "3"),))))

    assert reconciler.portfolio.get("AAPL") is None
    assert reconciler.portfolio.holdings == [_holding("MSFT", "3")]


def test_position_can_reopen_after_complete_close() -> None:
    reconciler = _reconciler()
    reconciler.apply(
        _success(_candidate((_holding("AAPL", "10"),)))
    )
    reconciler.apply(_success(_candidate(())))

    reconciler.apply(
        _success(_candidate((_holding("AAPL", "1.5"),)))
    )

    assert reconciler.portfolio.holdings == [_holding("AAPL", "1.5")]


def test_retrieved_portfolio_cannot_mutate_authoritative_truth() -> None:
    reconciler = _reconciler()
    original = _holding("AAPL", "10")
    reconciler.apply(_success(_candidate((original,))))

    external_portfolio = reconciler.portfolio
    external_portfolio.holdings.clear()
    external_portfolio.holdings.append(_holding("MSFT", "2"))

    assert reconciler.portfolio.holdings == [original]
