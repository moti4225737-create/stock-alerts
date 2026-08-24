from datetime import datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from unittest.mock import Mock

import pytest

from application.portfolio_truth_reconciler import PortfolioAcquisitionResult
from models.accepted_portfolio_truth import AcceptedPortfolioTruth
from models.candidate_portfolio_snapshot import (
    CandidatePortfolioSnapshot,
    SnapshotCompleteness,
)
from models.portfolio_holding import PortfolioHolding
from modules.file_portfolio_truth_store import PortfolioTruthStorageError


def _service_contract():
    return import_module(
        "application.portfolio_truth_service"
    ).PortfolioTruthService


def _holding(symbol: str, quantity: str) -> PortfolioHolding:
    return PortfolioHolding(symbol=symbol, quantity=Decimal(quantity))


def _source_as_of() -> datetime:
    return datetime(
        2026,
        8,
        24,
        15,
        0,
        tzinfo=timezone(timedelta(hours=3)),
    )


def _candidate(
    positions: tuple[PortfolioHolding, ...],
    completeness: SnapshotCompleteness = SnapshotCompleteness.COMPLETE,
) -> CandidatePortfolioSnapshot:
    return CandidatePortfolioSnapshot(
        positions=positions,
        source_as_of=_source_as_of(),
        completeness=completeness,
    )


def _success(candidate: CandidatePortfolioSnapshot):
    return PortfolioAcquisitionResult.succeeded(candidate)


def _accepted(
    positions: tuple[PortfolioHolding, ...],
) -> AcceptedPortfolioTruth:
    return AcceptedPortfolioTruth(
        positions=positions,
        source_as_of=_source_as_of(),
        accepted_at=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
    )


def _service(
    *,
    source_result=None,
    restored_truth=None,
    clock_value=None,
):
    PortfolioTruthService = _service_contract()
    source = Mock()
    source.acquire.return_value = (
        source_result
        if source_result is not None
        else PortfolioAcquisitionResult.failed()
    )
    store = Mock()
    store.load.return_value = restored_truth
    clock = Mock(
        return_value=(
            clock_value
            if clock_value is not None
            else datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc)
        )
    )
    return PortfolioTruthService(source, store, clock), source, store, clock


def test_portfolio_is_none_before_restore_or_acceptance() -> None:
    service, _, _, _ = _service()

    assert service.portfolio is None


def test_valid_persisted_truth_restores_without_source_acquisition() -> None:
    original = _accepted((_holding("AAPL", "7.99"),))
    service, source, _, _ = _service(restored_truth=original)

    restored = service.restore()

    assert restored is True
    assert service.portfolio is not None
    assert service.portfolio.holdings == [_holding("AAPL", "7.99")]
    source.acquire.assert_not_called()


def test_missing_persisted_truth_leaves_portfolio_absent() -> None:
    service, source, _, _ = _service(restored_truth=None)

    restored = service.restore()

    assert restored is False
    assert service.portfolio is None
    source.acquire.assert_not_called()


def test_persisted_accepted_empty_truth_restores_as_present_empty() -> None:
    service, _, _, _ = _service(restored_truth=_accepted(()))

    assert service.restore() is True
    assert service.portfolio is not None
    assert service.portfolio.holdings == []


def test_restore_storage_error_propagates_without_source_acquisition() -> None:
    service, source, store, _ = _service()
    store.load.side_effect = PortfolioTruthStorageError("corrupt")

    with pytest.raises(PortfolioTruthStorageError):
        service.restore()

    assert service.portfolio is None
    source.acquire.assert_not_called()


def test_invalid_restored_portfolio_is_reported_as_storage_corruption() -> None:
    duplicate_truth = _accepted(
        (
            _holding("AAPL", "1"),
            _holding("AAPL", "2"),
        )
    )
    service, source, _, _ = _service(restored_truth=duplicate_truth)

    with pytest.raises(PortfolioTruthStorageError) as error:
        service.restore()

    assert isinstance(error.value.__cause__, ValueError)
    assert service.portfolio is None
    source.acquire.assert_not_called()


def test_returned_restored_portfolio_cannot_mutate_service_truth() -> None:
    service, _, _, _ = _service(
        restored_truth=_accepted((_holding("AAPL", "10"),))
    )
    service.restore()

    external = service.portfolio
    external.holdings.clear()
    external.holdings.append(_holding("MSFT", "2"))

    assert service.portfolio.holdings == [_holding("AAPL", "10")]


def test_acquisition_failure_preserves_restored_truth_without_save() -> None:
    service, _, store, _ = _service(
        restored_truth=_accepted((_holding("AAPL", "10"),)),
        source_result=PortfolioAcquisitionResult.failed(),
    )
    service.restore()

    refreshed = service.refresh()

    assert refreshed is False
    assert service.portfolio.holdings == [_holding("AAPL", "10")]
    store.save.assert_not_called()


@pytest.mark.parametrize(
    "completeness",
    [SnapshotCompleteness.PARTIAL, SnapshotCompleteness.UNKNOWN],
)
def test_ineligible_candidate_preserves_truth_without_save(
    completeness,
) -> None:
    result = _success(_candidate((_holding("MSFT", "2"),), completeness))
    service, _, store, _ = _service(
        source_result=result,
        restored_truth=_accepted((_holding("AAPL", "10"),)),
    )
    service.restore()

    assert service.refresh() is False
    assert service.portfolio.holdings == [_holding("AAPL", "10")]
    store.save.assert_not_called()


def test_first_complete_candidate_is_persisted_then_published() -> None:
    candidate = _candidate((_holding("AAPL", "7.99"),))
    service, _, store, _ = _service(source_result=_success(candidate))
    portfolio_during_save = []

    def observe_save(_truth):
        portfolio_during_save.append(service.portfolio)

    store.save.side_effect = observe_save

    assert service.refresh() is True
    assert portfolio_during_save == [None]
    assert service.portfolio.holdings == [_holding("AAPL", "7.99")]
    store.save.assert_called_once()


def test_later_complete_candidate_replaces_current_truth() -> None:
    first = _success(_candidate((_holding("AAPL", "10"),)))
    second = _success(_candidate((_holding("MSFT", "3"),)))
    service, source, store, _ = _service(source_result=first)
    source.acquire.side_effect = [first, second]

    assert service.refresh() is True
    assert service.refresh() is True

    assert service.portfolio.holdings == [_holding("MSFT", "3")]
    assert source.acquire.call_count == 2
    assert store.save.call_count == 2


def test_complete_empty_becomes_present_authoritative_empty() -> None:
    result = _success(_candidate(()))
    service, _, store, _ = _service(source_result=result)

    assert service.refresh() is True
    assert service.portfolio is not None
    assert service.portfolio.holdings == []
    saved_truth = store.save.call_args.args[0]
    assert saved_truth.positions == ()


def test_complete_snapshots_replace_quantity_without_transaction_inference() -> None:
    results = [
        _success(_candidate((_holding("AAPL", "10"),))),
        _success(_candidate((_holding("AAPL", "15.5"),))),
        _success(_candidate((_holding("AAPL", "7.99"),))),
    ]
    service, source, _, _ = _service(source_result=results[0])
    source.acquire.side_effect = results

    assert service.refresh() is True
    assert service.refresh() is True
    assert service.refresh() is True

    assert service.portfolio.get("AAPL").quantity == Decimal("7.99")


def test_duplicate_candidate_fails_before_persistence() -> None:
    duplicate = _candidate(
        (
            _holding("AAPL", "1"),
            _holding("AAPL", "2"),
        )
    )
    service, _, store, clock = _service(source_result=_success(duplicate))

    with pytest.raises(ValueError, match="duplicate"):
        service.refresh()

    clock.assert_not_called()
    store.save.assert_not_called()
    assert service.portfolio is None


def test_save_failure_preserves_restored_truth() -> None:
    candidate = _candidate((_holding("MSFT", "2"),))
    service, _, store, _ = _service(
        source_result=_success(candidate),
        restored_truth=_accepted((_holding("AAPL", "10"),)),
    )
    service.restore()
    store.save.side_effect = PortfolioTruthStorageError("save failed")

    with pytest.raises(PortfolioTruthStorageError):
        service.refresh()

    assert service.portfolio.holdings == [_holding("AAPL", "10")]


def test_save_failure_on_first_boot_leaves_portfolio_absent() -> None:
    candidate = _candidate((_holding("AAPL", "10"),))
    service, _, store, _ = _service(source_result=_success(candidate))
    store.save.side_effect = PortfolioTruthStorageError("save failed")

    with pytest.raises(PortfolioTruthStorageError):
        service.refresh()

    assert service.portfolio is None


def test_accepted_at_uses_clock_once_and_is_normalized_to_utc() -> None:
    source_as_of = _source_as_of()
    candidate = CandidatePortfolioSnapshot(
        positions=(_holding("AAPL", "1"),),
        source_as_of=source_as_of,
        completeness=SnapshotCompleteness.COMPLETE,
    )
    clock_value = datetime(
        2026,
        8,
        24,
        15,
        30,
        tzinfo=timezone(timedelta(hours=3)),
    )
    service, _, store, clock = _service(
        source_result=_success(candidate),
        clock_value=clock_value,
    )

    assert service.refresh() is True

    saved_truth = store.save.call_args.args[0]
    assert saved_truth.accepted_at == datetime(
        2026, 8, 24, 12, 30, tzinfo=timezone.utc
    )
    assert saved_truth.accepted_at.utcoffset() == timedelta(0)
    assert saved_truth.source_as_of is source_as_of
    clock.assert_called_once_with()


def test_naive_clock_fails_before_save_and_publication() -> None:
    candidate = _candidate((_holding("AAPL", "1"),))
    service, _, store, clock = _service(
        source_result=_success(candidate),
        clock_value=datetime(2026, 8, 24, 12, 0),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        service.refresh()

    clock.assert_called_once_with()
    store.save.assert_not_called()
    assert service.portfolio is None


@pytest.mark.parametrize(
    "source_result",
    [
        PortfolioAcquisitionResult.failed(),
        _success(_candidate((), SnapshotCompleteness.PARTIAL)),
        _success(_candidate((), SnapshotCompleteness.UNKNOWN)),
    ],
)
def test_first_boot_no_change_results_leave_portfolio_absent(
    source_result,
) -> None:
    service, _, store, _ = _service(source_result=source_result)

    assert service.restore() is False
    assert service.refresh() is False
    assert service.portfolio is None
    store.save.assert_not_called()
