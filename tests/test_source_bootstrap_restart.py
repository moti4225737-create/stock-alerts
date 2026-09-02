import json
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from application.source_bootstrap_application import SourceBootstrapApplication
from models.company_identity import CompanyIdentity
from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import (
    OpeningFactCandidate,
    OpeningFactDecision,
    OpeningFactDisposition,
    OpeningResearchResult,
    SourceBootstrapLifecycle,
    SourceBootstrapResearchRequest,
    SourceBootstrapState,
)
from models.source_evidence import SourceEvidence
from modules.file_source_bootstrap_store import (
    FileSourceBootstrapStore,
    SourceBootstrapStorageError,
)


TIME_ZERO = datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc)


def _holding(symbol: str = "ONDS") -> PortfolioHolding:
    return PortfolioHolding(symbol=symbol, quantity=Decimal("25"))


def _identity(symbol: str = "ONDS") -> CompanyIdentity:
    return CompanyIdentity(
        ticker=symbol,
        company_name="Ondas Holdings Inc.",
        cik="0001646188",
        exchange="NASDAQ",
    )


def _candidate() -> OpeningFactCandidate:
    return OpeningFactCandidate(
        fact="Cash and cash equivalents were $120 million.",
        category="sec_filing",
        evidence=(SourceEvidence(
            source_url=(
                "https://www.sec.gov/Archives/edgar/data/1646188/"
                "000164618826000001/onds-20251231.htm"
            ),
            text="Provider research evidence.",
            locator="Item 8",
        ),),
    )


def _ready_state(holding: PortfolioHolding | None = None) -> SourceBootstrapState:
    owned_holding = holding or _holding()
    candidate = _candidate()
    return SourceBootstrapState(
        request=SourceBootstrapResearchRequest(
            holding=owned_holding,
            time_zero=TIME_ZERO,
        ),
        verified_identity=_identity(owned_holding.symbol),
        research_output=OpeningResearchResult(
            candidates=(candidate,),
            completed_successfully=True,
        ),
        decisions=(OpeningFactDecision(
            candidate=candidate,
            disposition=OpeningFactDisposition.VERIFIED,
        ),),
    )


def test_clean_ready_state_round_trips_for_authoritative_target_holding(
    tmp_path,
) -> None:
    path = tmp_path / "source-bootstrap-state.json"
    store = FileSourceBootstrapStore(path)
    original = _ready_state()
    store.save(original)

    restored = store.load(target_holding=_holding())

    assert restored == original
    assert restored.time_zero == TIME_ZERO
    assert restored.verified_identity == original.verified_identity
    assert restored.research_output == original.research_output
    assert restored.decisions == original.decisions
    assert restored.lifecycle is SourceBootstrapLifecycle.READY


def test_store_rejects_ready_state_owned_by_another_holding(tmp_path) -> None:
    store = FileSourceBootstrapStore(tmp_path / "source-bootstrap-state.json")
    ondas_state = _ready_state(_holding("ONDS"))
    store.save(ondas_state)

    assert store.load(target_holding=_holding("AAPL")) is None
    assert store.load(target_holding=_holding("ONDS")) == ondas_state


def test_clean_persisted_shape_contains_only_approved_opening_state(
    tmp_path,
) -> None:
    path = tmp_path / "source-bootstrap-state.json"
    FileSourceBootstrapStore(path).save(_ready_state())

    state_files = list(path.glob("*.json"))
    assert len(state_files) == 1
    payload = json.loads(state_files[0].read_text(encoding="utf-8"))

    assert set(payload) == {
        "schema", "version", "request", "verified_identity",
        "research_output", "decisions",
    }
    assert payload["schema"] == "stock-sentinel.source-bootstrap"
    assert payload["version"] == 2
    assert set(payload["request"]) == {"holding", "time_zero"}
    assert set(payload["verified_identity"]) == {
        "ticker", "company_name", "cik", "exchange",
    }
    assert set(payload["research_output"]) == {
        "completed_successfully", "candidates",
    }
    candidate = payload["research_output"]["candidates"][0]
    assert set(candidate) == {"fact", "category", "evidence"}
    assert set(candidate["evidence"][0]) == {
        "source_url", "text", "locator",
    }
    assert payload["decisions"] == [{
        "candidate_index": 0,
        "disposition": "verified",
    }]
    serialized = json.dumps(payload)
    for obsolete in (
        "lifecycle", "accepted_source_map", "profile", "relationships",
        "monitoring_requirements", "unresolved_requirements", "role",
        "resolution", "material",
    ):
        assert obsolete not in serialized


def test_legacy_version_one_is_rejected_without_deserialization(tmp_path) -> None:
    path = tmp_path / "source-bootstrap-state.json"
    store = FileSourceBootstrapStore(path)
    store.save(_ready_state())
    state_files = list(path.glob("*.json"))
    assert len(state_files) == 1
    state_files[0].write_text(json.dumps({
        "schema": "stock-sentinel.source-bootstrap",
        "version": 1,
        "accepted_source_map": {"identity": {}},
    }), encoding="utf-8")

    with pytest.raises(
        SourceBootstrapStorageError,
        match="Unable to load Source Bootstrap state",
    ):
        store.load(target_holding=_holding())


def test_application_restores_only_matching_authoritative_holding() -> None:
    target_holding = _holding()
    restored = _ready_state(target_holding)
    store = Mock()
    store.load.return_value = restored
    portfolio_service = Mock()
    portfolio_service.introduced_holdings = ()
    research = Mock()
    identity_resolver = Mock()
    opening_verification = Mock()
    application = SourceBootstrapApplication(
        portfolio_service=portfolio_service,
        store=store,
    )

    result = application.run(
        target_holding=target_holding,
        research=research,
        identity_resolver=identity_resolver,
        opening_verification=opening_verification,
    )

    assert result is restored
    store.load.assert_called_once_with(target_holding=target_holding)
    portfolio_service.begin_source_bootstrap.assert_not_called()
    research.assert_not_called()
    identity_resolver.resolve.assert_not_called()
    opening_verification.assert_not_called()
    store.save.assert_not_called()


def test_application_restores_same_symbol_after_position_values_change(
    tmp_path,
) -> None:
    original_holding = PortfolioHolding(
        symbol="ONDS",
        quantity=Decimal("25"),
        average_cost=4.0,
    )
    updated_holding = PortfolioHolding(
        symbol="ONDS",
        quantity=Decimal("40"),
        average_cost=6.0,
    )
    original = _ready_state(original_holding)
    store = FileSourceBootstrapStore(tmp_path / "opening-states")
    store.save(original)
    portfolio_service = Mock()
    portfolio_service.introduced_holdings = ()
    application = SourceBootstrapApplication(
        portfolio_service=portfolio_service,
        store=store,
    )

    restored = application.run(
        target_holding=updated_holding,
        research=Mock(),
        identity_resolver=Mock(),
        opening_verification=Mock(),
    )

    assert restored == original
    assert restored.time_zero == original.time_zero
    portfolio_service.begin_source_bootstrap.assert_not_called()


def test_application_builds_and_persists_clean_ready_state() -> None:
    target_holding = _holding()
    request = SourceBootstrapResearchRequest(
        holding=target_holding,
        time_zero=TIME_ZERO,
    )
    candidate = _candidate()
    research_output = OpeningResearchResult(
        candidates=(candidate,),
        completed_successfully=True,
    )
    identity = _identity()
    store = Mock()
    store.load.return_value = None
    portfolio_service = Mock()
    portfolio_service.introduced_holdings = (target_holding,)

    def begin_source_bootstrap(*, target_holding, research):
        assert target_holding == request.holding
        return SourceBootstrapState(
            request=request,
            research_output=research(request),
        )

    portfolio_service.begin_source_bootstrap.side_effect = begin_source_bootstrap
    research = Mock(return_value=research_output)
    identity_resolver = Mock()
    identity_resolver.resolve.return_value = identity

    def verify(state: SourceBootstrapState):
        assert state.verified_identity is identity
        assert state.research_output is research_output
        return (OpeningFactDecision(
            candidate=candidate,
            disposition=OpeningFactDisposition.VERIFIED,
        ),)

    opening_verification = Mock(side_effect=verify)
    application = SourceBootstrapApplication(
        portfolio_service=portfolio_service,
        store=store,
    )

    result = application.run(
        target_holding=target_holding,
        research=research,
        identity_resolver=identity_resolver,
        opening_verification=opening_verification,
    )

    assert result.lifecycle is SourceBootstrapLifecycle.READY
    assert result.request.holding == target_holding
    assert result.verified_identity is identity
    assert result.research_output is research_output
    assert result.decisions[0].candidate is candidate
    store.load.assert_not_called()
    portfolio_service.begin_source_bootstrap.assert_called_once()
    identity_resolver.resolve.assert_called_once_with("ONDS")
    research.assert_called_once_with(request, known_identity=identity)
    opening_verification.assert_called_once()
    store.save.assert_called_once_with(result)
    portfolio_service.record_source_bootstrap.assert_called_once_with(result)


def test_application_persists_and_restores_learning_with_original_time_zero(
    tmp_path,
) -> None:
    target_holding = _holding()
    request = SourceBootstrapResearchRequest(
        holding=target_holding,
        time_zero=TIME_ZERO,
    )
    research_output = OpeningResearchResult(
        candidates=(),
        completed_successfully=True,
    )
    store = FileSourceBootstrapStore(tmp_path / "opening-states")
    first_service = Mock()
    first_service.introduced_holdings = (target_holding,)

    def begin_source_bootstrap(*, target_holding, research):
        assert target_holding == request.holding
        return SourceBootstrapState(
            request=request,
            research_output=research(request),
        )

    first_service.begin_source_bootstrap.side_effect = begin_source_bootstrap
    identity_resolver = Mock()
    identity_resolver.resolve.return_value = _identity()
    first_application = SourceBootstrapApplication(
        portfolio_service=first_service,
        store=store,
    )

    learning = first_application.run(
        target_holding=target_holding,
        research=Mock(return_value=research_output),
        identity_resolver=identity_resolver,
        opening_verification=Mock(return_value=()),
    )

    assert learning.is_ready is False
    assert learning.time_zero == TIME_ZERO
    first_service.record_source_bootstrap.assert_called_once_with(learning)

    restarted_service = Mock()
    restarted_service.introduced_holdings = ()
    restarted_research = Mock()
    restarted_identity = Mock()
    restarted_verification = Mock()
    restarted_application = SourceBootstrapApplication(
        portfolio_service=restarted_service,
        store=store,
    )

    restored = restarted_application.run(
        target_holding=target_holding,
        research=restarted_research,
        identity_resolver=restarted_identity,
        opening_verification=restarted_verification,
    )

    assert restored == learning
    assert restored.time_zero == TIME_ZERO
    assert restored.is_ready is False
    restarted_service.begin_source_bootstrap.assert_not_called()
    restarted_research.assert_not_called()
    restarted_identity.resolve.assert_not_called()
    restarted_verification.assert_not_called()


def test_application_fails_closed_if_bootstrap_state_owns_wrong_holding() -> None:
    target_holding = _holding("AAPL")
    store = Mock()
    store.load.return_value = None
    portfolio_service = Mock()
    portfolio_service.introduced_holdings = (target_holding,)
    portfolio_service.begin_source_bootstrap.return_value = replace(
        _ready_state(_holding("ONDS")), decisions=(),
    )
    application = SourceBootstrapApplication(
        portfolio_service=portfolio_service,
        store=store,
    )

    with pytest.raises(RuntimeError, match="target holding"):
        application.run(
            target_holding=target_holding,
            research=Mock(),
            identity_resolver=Mock(),
            opening_verification=Mock(),
        )

    store.save.assert_not_called()


def test_identity_failure_prevents_research_verification_and_save() -> None:
    target_holding = _holding()
    request = SourceBootstrapResearchRequest(
        holding=target_holding,
        time_zero=TIME_ZERO,
    )
    store = Mock()
    store.load.return_value = None
    portfolio_service = Mock()
    portfolio_service.introduced_holdings = (target_holding,)

    def begin_source_bootstrap(*, target_holding, research):
        assert target_holding == request.holding
        research(request)

    portfolio_service.begin_source_bootstrap.side_effect = begin_source_bootstrap
    identity_error = RuntimeError("identity unavailable")
    identity_resolver = Mock()
    identity_resolver.resolve.side_effect = identity_error
    research = Mock()
    opening_verification = Mock()
    application = SourceBootstrapApplication(
        portfolio_service=portfolio_service,
        store=store,
    )

    with pytest.raises(RuntimeError, match="identity unavailable"):
        application.run(
            target_holding=target_holding,
            research=research,
            identity_resolver=identity_resolver,
            opening_verification=opening_verification,
        )

    research.assert_not_called()
    opening_verification.assert_not_called()
    store.save.assert_not_called()
