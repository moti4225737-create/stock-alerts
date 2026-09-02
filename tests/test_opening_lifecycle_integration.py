from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from application.portfolio_truth_reconciler import PortfolioAcquisitionResult
from application.portfolio_truth_service import PortfolioTruthService
from application.source_runtime_factory import SourceRuntimeFactory
from engines.intelligence_pipeline import IntelligencePipeline
from models.accepted_portfolio_truth import AcceptedPortfolioTruth
from models.candidate_portfolio_snapshot import (
    CandidatePortfolioSnapshot,
    SnapshotCompleteness,
)
from models.company_identity import CompanyIdentity
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import (
    OpeningFactCandidate,
    OpeningFactDecision,
    OpeningFactDisposition,
    OpeningResearchResult,
    SourceBootstrapResearchRequest,
    SourceBootstrapState,
)
from models.source_evidence import SourceEvidence
from modules.file_source_bootstrap_store import FileSourceBootstrapStore


BASE_TIME = datetime(2026, 9, 2, 9, 0, tzinfo=timezone.utc)


def _holding(
    symbol: str,
    quantity: str = "1",
    average_cost: float | None = None,
) -> PortfolioHolding:
    return PortfolioHolding(
        symbol=symbol,
        quantity=Decimal(quantity),
        average_cost=average_cost,
    )


def _snapshot(
    *holdings: PortfolioHolding,
    completeness: SnapshotCompleteness = SnapshotCompleteness.COMPLETE,
) -> PortfolioAcquisitionResult:
    return PortfolioAcquisitionResult.succeeded(
        CandidatePortfolioSnapshot(
            positions=holdings,
            source_as_of=BASE_TIME,
            completeness=completeness,
        )
    )


def _accepted(*holdings: PortfolioHolding) -> AcceptedPortfolioTruth:
    return AcceptedPortfolioTruth(
        positions=holdings,
        source_as_of=BASE_TIME,
        accepted_at=BASE_TIME,
    )


class _AdvancingClock:
    def __init__(self) -> None:
        self._calls = 0

    def __call__(self) -> datetime:
        value = BASE_TIME + timedelta(seconds=self._calls)
        self._calls += 1
        return value


def _service(*, restored=(), results=()):
    source = Mock()
    source.acquire.side_effect = list(results)
    store = Mock()
    store.load.return_value = _accepted(*restored)
    service = PortfolioTruthService(source, store, _AdvancingClock())
    assert service.restore() is True
    return service, source


def _learning_state(holding: PortfolioHolding, time_zero=BASE_TIME):
    return SourceBootstrapState(
        request=SourceBootstrapResearchRequest(
            holding=holding,
            time_zero=time_zero,
        ),
        research_output=OpeningResearchResult(
            candidates=(),
            completed_successfully=True,
        ),
    )


def _ready_state(holding: PortfolioHolding, time_zero=BASE_TIME):
    candidate = OpeningFactCandidate(
        fact=f"{holding.symbol} filed an authoritative SEC report.",
        category="sec_filing",
        evidence=(SourceEvidence(
            source_url=(
                "https://www.sec.gov/Archives/edgar/data/1/"
                "000000000126000001/report.htm"
            ),
            text="Independently reconstructed SEC evidence.",
            locator="Item 1",
        ),),
    )
    return SourceBootstrapState(
        request=SourceBootstrapResearchRequest(
            holding=holding,
            time_zero=time_zero,
        ),
        verified_identity=CompanyIdentity(
            ticker=holding.symbol,
            company_name=f"{holding.symbol} Company",
            cik="0000000001",
            exchange="NASDAQ",
        ),
        research_output=OpeningResearchResult(
            candidates=(candidate,),
            completed_successfully=True,
        ),
        decisions=(OpeningFactDecision(
            candidate=candidate,
            disposition=OpeningFactDisposition.VERIFIED,
        ),),
    )


def test_zero_introductions_and_position_updates_keep_existing_lifecycle() -> None:
    original = _holding("A", "10", 5.0)
    updated = _holding("A", "12", 6.0)
    service, _ = _service(
        restored=(original,),
        results=(_snapshot(updated),),
    )
    research = Mock()

    assert service.refresh() is True

    assert service.introduced_holdings == ()
    assert service.begin_source_bootstrap(
        target_holding=updated,
        research=research,
    ) is None
    assert service.portfolio.holdings == [updated]
    research.assert_not_called()


def test_bootstrap_requires_an_explicit_target_holding() -> None:
    holding = _holding("C")
    service, _ = _service(results=(_snapshot(holding),))
    assert service.refresh() is True

    with pytest.raises(TypeError, match="target_holding"):
        service.begin_source_bootstrap(research=Mock())


def test_multiple_introductions_are_independently_addressable() -> None:
    existing = (_holding("A"), _holding("B"))
    introduced = (_holding("C"), _holding("D"), _holding("E"))
    service, _ = _service(
        restored=existing,
        results=(_snapshot(*existing, *introduced),),
    )
    assert service.refresh() is True

    states = {
        holding.symbol: service.begin_source_bootstrap(
            target_holding=holding,
            research=lambda request: OpeningResearchResult(
                candidates=(),
                completed_successfully=True,
            ),
        )
        for holding in introduced
    }

    assert service.introduced_holdings == introduced
    assert set(states) == {"C", "D", "E"}
    assert all(
        state.request.holding.symbol == symbol
        for symbol, state in states.items()
    )
    assert len({state.time_zero for state in states.values()}) == 3


def test_one_introduction_failure_does_not_block_other_openings() -> None:
    introduced = (_holding("C"), _holding("D"), _holding("E"))
    service, _ = _service(results=(_snapshot(*introduced),))
    assert service.refresh() is True

    completed = {}
    for holding in introduced:
        research = (
            Mock(side_effect=RuntimeError("research failed"))
            if holding.symbol == "D"
            else Mock(return_value=OpeningResearchResult(
                candidates=(),
                completed_successfully=True,
            ))
        )
        try:
            completed[holding.symbol] = service.begin_source_bootstrap(
                target_holding=holding,
                research=research,
            )
        except RuntimeError as exc:
            assert holding.symbol == "D"
            assert str(exc) == "research failed"

    assert set(completed) == {"C", "E"}
    assert completed["C"].request.holding == introduced[0]
    assert completed["E"].request.holding == introduced[2]


def test_failed_refresh_preserves_the_active_opening_lifecycle() -> None:
    holding = _holding("C")
    service, source = _service(
        results=(_snapshot(holding), PortfolioAcquisitionResult.failed()),
    )
    assert service.refresh() is True
    first = service.begin_source_bootstrap(
        target_holding=holding,
        research=Mock(return_value=OpeningResearchResult(
            candidates=(), completed_successfully=True
        )),
    )

    assert service.refresh() is False
    restarted = service.begin_source_bootstrap(
        target_holding=holding,
        research=Mock(),
    )

    assert restarted is first
    assert restarted.time_zero == first.time_zero
    assert source.acquire.call_count == 2


def test_removal_and_reintroduction_creates_a_new_lifecycle() -> None:
    holding = _holding("C")
    service, _ = _service(
        results=(
            _snapshot(holding),
            _snapshot(),
            _snapshot(holding),
        ),
    )
    research = Mock(return_value=OpeningResearchResult(
        candidates=(), completed_successfully=True
    ))

    assert service.refresh() is True
    first = service.begin_source_bootstrap(
        target_holding=holding,
        research=research,
    )
    assert service.refresh() is True
    assert service.begin_source_bootstrap(
        target_holding=holding,
        research=Mock(),
    ) is None
    assert service.refresh() is True
    second = service.begin_source_bootstrap(
        target_holding=holding,
        research=research,
    )

    assert second is not first
    assert second.time_zero > first.time_zero
    assert research.call_count == 2


def test_position_update_reuses_active_opening_state_and_time_zero() -> None:
    original = _holding("C", "1", 5.0)
    updated = _holding("C", "2", 7.0)
    service, _ = _service(
        results=(_snapshot(original), _snapshot(updated)),
    )
    research = Mock(return_value=OpeningResearchResult(
        candidates=(), completed_successfully=True
    ))

    assert service.refresh() is True
    first = service.begin_source_bootstrap(
        target_holding=original,
        research=research,
    )
    assert service.refresh() is True
    second = service.begin_source_bootstrap(
        target_holding=updated,
        research=research,
    )

    assert second is first
    assert second.time_zero == first.time_zero
    assert service.portfolio.holdings == [updated]
    research.assert_called_once()


def test_store_persists_multiple_holdings_without_overwrite(tmp_path) -> None:
    store = FileSourceBootstrapStore(tmp_path / "opening-states")
    c_state = _ready_state(_holding("C"))
    d_state = _ready_state(_holding("D"), BASE_TIME + timedelta(seconds=1))

    store.save(c_state)
    store.save(d_state)

    assert store.load(target_holding=_holding("C")) == c_state
    assert store.load(target_holding=_holding("D")) == d_state


def test_learning_state_round_trips_without_becoming_ready(tmp_path) -> None:
    store = FileSourceBootstrapStore(tmp_path / "opening-states")
    original = _learning_state(_holding("C"))

    store.save(original)
    restored = store.load(target_holding=_holding("C"))

    assert restored == original
    assert restored.time_zero == original.time_zero
    assert restored.is_ready is False


def test_dynamic_runtime_view_isolates_learning_holding() -> None:
    holdings = tuple(_holding(symbol) for symbol in ("A", "B", "C", "D", "E"))
    authoritative = Portfolio(holdings)
    states = {
        "C": _ready_state(holdings[2]),
        "D": _learning_state(holdings[3]),
        "E": _ready_state(holdings[4]),
    }

    def eligible_portfolio() -> Portfolio:
        return Portfolio(
            holding
            for holding in authoritative.holdings
            if holding.symbol not in states or states[holding.symbol].is_ready
        )

    factory = SourceRuntimeFactory(
        portfolio_provider=eligible_portfolio,
        telegram_sender=Mock(),
        enrichment_service=Mock(),
        telegram_transport=Mock(),
        notification_history=Mock(),
    )

    runtime = factory(IntelligencePipeline(providers=[]))

    assert [holding.symbol for holding in runtime._portfolio.holdings] == [
        "A", "B", "C", "E"
    ]
    assert [holding.symbol for holding in authoritative.holdings] == [
        "A", "B", "C", "D", "E"
    ]
