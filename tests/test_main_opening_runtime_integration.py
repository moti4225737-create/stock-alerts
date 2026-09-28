from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

import pytest

import main
from application.portfolio_truth_reconciler import PortfolioAcquisitionResult
from application.portfolio_truth_service import PortfolioTruthService
from application.sec_source_bootstrap_acceptance_producer import (
    SECSourceBootstrapAcceptanceProducer,
)
from application.source_bootstrap_application import SourceBootstrapApplication
from application.source_bootstrap_researcher import (
    BoundedResearchLimits,
    BoundedSourceBootstrapResearcher,
)
from models.accepted_portfolio_truth import AcceptedPortfolioTruth
from models.candidate_portfolio_snapshot import (
    CandidatePortfolioSnapshot,
    SnapshotCompleteness,
)
from models.company_identity import CompanyIdentity
from models.event import Event
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
from models.source_document import SourceDocument
from models.source_finding_candidate import SourceFindingCandidate
from modules.file_source_bootstrap_store import FileSourceBootstrapStore
from modules.file_portfolio_truth_store import FilePortfolioTruthStore


TIME_ZERO = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)


def test_real_opening_wiring_verifies_history_before_ready_without_live_admission(
    monkeypatch, tmp_path,
):
    from modules.sec_provider import SECProvider

    monkeypatch.setenv("SEC_USER_AGENT", "unit-test test@example.test")
    monkeypatch.chdir(tmp_path)
    holding = _holding("WDS")
    truth_store = FilePortfolioTruthStore(tmp_path / "truth.json")
    truth_store.save(AcceptedPortfolioTruth(
        positions=(holding,), source_as_of=TIME_ZERO, accepted_at=TIME_ZERO,
    ))
    service = PortfolioTruthService(Mock(), truth_store, lambda: TIME_ZERO)
    assert service.restore()
    observation = Mock()
    observation.load.return_value = None
    provider = SECProvider(time_zero_for=lambda symbol: None,
                           source_observation_store=observation)
    url = "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/report.htm"
    fact = "Cash and cash equivalents were $120 million."

    def get(url_arg, **kwargs):
        response = Mock()
        if url_arg == provider.TICKERS_URL:
            response.json.return_value = {"0": {"ticker": "WDS", "cik_str": 1}}
        elif url_arg == provider.SUBMISSIONS_URL.format(cik="0000000001"):
            response.json.return_value = {"filings": {"recent": {
                "form": ["20-F"], "filingDate": ["2026-03-01"],
                "acceptanceDateTime": ["2026-03-01T12:00:00Z"],
                "accessionNumber": ["0000000001-26-000001"],
                "primaryDocument": ["report.htm"],
            }}}
        elif url_arg.endswith("company_tickers_exchange.json"):
            response.json.return_value = {
                "fields": ["cik", "name", "ticker", "exchange"],
                "data": [[1, "WDS Company", "WDS", "NYSE"]],
            }
        elif url_arg == url:
            response.text = "<html><body><p>" + fact + "</p></body></html>"
        else:
            raise AssertionError("Unexpected HTTP target")
        return response

    monkeypatch.setattr(main.requests, "get", Mock(side_effect=get))
    monkeypatch.setattr(main.requests, "post", Mock(side_effect=AssertionError("No real research")))
    app, _, identity, verification, store = main._build_opening_components(
        portfolio_service=service, providers={"SEC": provider},
    )
    assert store.load(target_holding=holding) is None
    candidate = OpeningFactCandidate(fact=fact, category="sec_filing", evidence=(
        SourceEvidence(source_url=url, text="AI proposal only"),
    ))
    state = app.run(
        target_holding=holding,
        research=Mock(return_value=OpeningResearchResult((candidate,), True)),
        identity_resolver=identity, opening_verification=verification,
        admission_reason="current authoritative holding missing Opening admission state",
    )
    assert state.is_ready
    assert state.time_zero == TIME_ZERO
    assert store.load(target_holding=holding).is_ready
    assert service.portfolio.get("WDS") == holding
    observation.load.assert_not_called()
    observation.save.assert_not_called()
    assert provider.fetch_events("WDS") == []
    assert observation.save.call_args.args[0].pending == ()
    assert observation.save.call_args.args[0].objects
    main.requests.post.assert_not_called()


def _holding(symbol: str) -> PortfolioHolding:
    return PortfolioHolding(symbol=symbol, quantity=1)


def _learning(holding: PortfolioHolding) -> SourceBootstrapState:
    return SourceBootstrapState(
        request=SourceBootstrapResearchRequest(
            holding=holding,
            time_zero=TIME_ZERO,
        ),
        research_output=OpeningResearchResult(
            candidates=(),
            completed_successfully=True,
        ),
    )


def _ready(holding: PortfolioHolding) -> SourceBootstrapState:
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
            time_zero=TIME_ZERO,
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


def _prepare_main(monkeypatch, *, portfolio, introduced):
    monkeypatch.setenv("AUTONOMOUS_MAX_CYCLES", "2")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-semantic-model")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
    monkeypatch.setenv("SEC_USER_AGENT", "test-sec-user-agent")
    monkeypatch.setenv("LIFEGUARD_PING_URL", "https://example.test/lifeguard")

    provider_manager = Mock()
    provider_manager.build_named.return_value = {"SEC": Mock()}
    monkeypatch.setattr(main, "ProviderManager", Mock(return_value=provider_manager))
    monkeypatch.setattr(
        main,
        "build_default_source_acquisition_policies",
        Mock(return_value={}),
    )
    monkeypatch.setattr(main, "JsonFilePortfolioSource", Mock())
    monkeypatch.setattr(main, "FilePortfolioTruthStore", Mock())

    portfolio_service = Mock()
    portfolio_service.portfolio = portfolio
    portfolio_service.introduced_holdings = introduced
    monkeypatch.setattr(
        main,
        "PortfolioTruthService",
        Mock(return_value=portfolio_service),
    )

    opening_application = Mock()
    monkeypatch.setattr(
        main,
        "SourceBootstrapApplication",
        Mock(return_value=opening_application),
        raising=False,
    )
    opening_store = Mock()
    opening_store.load.return_value = None
    monkeypatch.setattr(
        main,
        "FileSourceBootstrapStore",
        Mock(return_value=opening_store),
        raising=False,
    )

    runtime_factory = Mock(return_value=Mock())
    monkeypatch.setattr(main, "SourceRuntimeFactory", runtime_factory)
    loop = Mock()
    monkeypatch.setattr(main, "build_autonomous_loop", Mock(return_value=loop))

    return portfolio_service, opening_application, runtime_factory, loop


def _prepare_o28_entry(monkeypatch):
    """Reuse main wiring setup, retaining real portfolio and Opening ordering."""
    holding = _holding("WDS")
    _, _, _, loop = _prepare_main(
        monkeypatch, portfolio=Portfolio([holding]), introduced=(holding,),
    )
    events = []

    def boundary(name, result=None):
        def record(*args, **kwargs):
            events.append(name)
            return result
        return Mock(side_effect=record)

    source = main.JsonFilePortfolioSource.return_value
    source.acquire.return_value = PortfolioAcquisitionResult.succeeded(
        CandidatePortfolioSnapshot(
            positions=(holding,), source_as_of=TIME_ZERO,
            completeness=SnapshotCompleteness.COMPLETE,
        )
    )
    truth_store = main.FilePortfolioTruthStore.return_value
    truth_store.load.return_value = None
    truth_store.save = boundary("portfolio_save")
    monkeypatch.setattr(main, "PortfolioTruthService", PortfolioTruthService)
    monkeypatch.setattr(main, "SourceBootstrapApplication", SourceBootstrapApplication)
    opening_store = main.FileSourceBootstrapStore.return_value
    opening_store.save = boundary("opening_save")
    opening_store.invalidate = boundary("opening_invalidate")

    def get(url, **kwargs):
        if url.endswith("company_tickers_exchange.json"):
            events.append("sec_http")
            response = Mock()
            response.json.return_value = {
                "fields": ["cik", "name", "ticker", "exchange"],
                "data": [[1, "WDS Test Issuer", "WDS", "NYSE"]],
            }
            return response
        events.append("unexpected_http_get")
        raise AssertionError("Unexpected HTTP GET")

    def post(url, **kwargs):
        if url == "https://api.perplexity.ai/v1/sonar":
            events.append("perplexity_http")
            response = Mock(status_code=200)
            response.json.return_value = {
                "choices": [{"message": {"content": '{"candidates": []}'}}],
            }
            return response
        events.append("unexpected_http_post")
        raise AssertionError("Unexpected HTTP POST")

    monkeypatch.setattr(main.requests, "get", Mock(side_effect=get))
    monkeypatch.setattr(main.requests, "post", Mock(side_effect=post))
    client = Mock()
    client.responses.parse = boundary("openai")
    client.chat.completions.create = boundary("openai")
    monkeypatch.setattr(main, "OpenAI", Mock(return_value=client))
    monkeypatch.setattr(main, "send_telegram", boundary("telegram"))
    monkeypatch.setattr(
        main, "HealthchecksWorkEvidenceReporter",
        Mock(return_value=boundary("healthchecks")),
    )
    observation = Mock()
    observation.save = boundary("observation_write")
    monkeypatch.setattr(main, "FileSourceObservationStore", Mock(return_value=observation))
    history = Mock()
    history.record = boundary("notification_write")
    monkeypatch.setattr(main, "NotificationHistory", Mock(return_value=history))
    for provider in main.ProviderManager.return_value.build_named.return_value.values():
        provider.fetch_events = boundary("provider_execution", [])
        provider.fetch_opening_evidence = boundary("provider_execution", [])
    loop.run = boundary("runtime_execution")
    return events, loop, opening_store


@pytest.mark.parametrize("value", [None, "0", "-1", "not-an-integer"],
                         ids=["missing", "zero", "negative", "non-numeric"])
def test_o28_main_rejects_invalid_bound_before_any_consequence(monkeypatch, value):
    events, _, _ = _prepare_o28_entry(monkeypatch)
    if value is None:
        monkeypatch.delenv("AUTONOMOUS_MAX_CYCLES", raising=False)
    else:
        monkeypatch.setenv("AUTONOMOUS_MAX_CYCLES", value)

    with pytest.raises(KeyError if value is None else ValueError):
        main.main()
    events.append("bound_rejected")

    assert events == ["bound_rejected"], f"Consequences before rejection: {events}"


def test_o28_main_valid_bound_reaches_real_opening_then_mocked_runtime(monkeypatch):
    events, loop, opening_store = _prepare_o28_entry(monkeypatch)
    monkeypatch.setenv("AUTONOMOUS_MAX_CYCLES", "1")

    main.main()

    assert events == [
        "opening_invalidate", "portfolio_save", "sec_http", "perplexity_http",
        "opening_save", "runtime_execution",
    ]
    state = opening_store.save.call_args.args[0]
    assert state.request.holding.symbol == "WDS"
    assert state.verified_identity.ticker == "WDS"
    assert state.research_output.completed_successfully
    loop.run.assert_called_once_with(max_cycles=1)


def test_main_processes_multiple_introductions_before_runtime_creation(
    monkeypatch,
) -> None:
    a, b, c, d = tuple(_holding(symbol) for symbol in "ABCD")
    calls = []
    _, opening_application, runtime_factory, loop = _prepare_main(
        monkeypatch,
        portfolio=Portfolio([a, b, c, d]),
        introduced=(c, d),
    )
    main.FileSourceBootstrapStore.return_value.load.side_effect = (
        lambda *, target_holding: _ready(target_holding)
    )
    opening_application.run.side_effect = lambda **kwargs: (
        calls.append(f"opening:{kwargs['target_holding'].symbol}")
        or (_ready(c) if kwargs["target_holding"] == c else _learning(d))
    )
    runtime_factory.side_effect = lambda **kwargs: (
        calls.append("runtime_factory") or Mock()
    )

    main.main()

    assert [item.kwargs["target_holding"] for item in opening_application.run.call_args_list] == [
        c,
        d,
    ]
    assert calls == ["opening:C", "opening:D", "runtime_factory"]
    loop.run.assert_called_once_with(max_cycles=2)


def test_main_runtime_provider_excludes_learning_without_changing_truth(
    monkeypatch,
) -> None:
    a, b, c, d = tuple(_holding(symbol) for symbol in "ABCD")
    authoritative = Portfolio([a, b, c, d])
    portfolio_service, opening_application, runtime_factory, _ = _prepare_main(
        monkeypatch,
        portfolio=authoritative,
        introduced=(c, d),
    )
    main.FileSourceBootstrapStore.return_value.load.side_effect = (
        lambda *, target_holding: _ready(target_holding)
    )
    opening_application.run.side_effect = [_ready(c), _learning(d)]

    main.main()

    portfolio_provider = runtime_factory.call_args.kwargs["portfolio_provider"]
    runtime_portfolio = portfolio_provider()
    assert [holding.symbol for holding in runtime_portfolio.holdings] == [
        "A", "B", "C"
    ]
    assert [holding.symbol for holding in portfolio_service.portfolio.holdings] == [
        "A", "B", "C", "D"
    ]
    assert opening_application.run.call_count == 2


def test_main_missing_opening_state_never_admits_failed_legacy_adoption(
    monkeypatch,
) -> None:
    existing = Portfolio([_holding("A"), _holding("B")])
    service, opening_application, runtime_factory, loop = _prepare_main(
        monkeypatch,
        portfolio=existing,
        introduced=(),
    )
    opening_application.run.side_effect = RuntimeError("Opening unavailable")

    main.main()

    portfolio_provider = runtime_factory.call_args.kwargs["portfolio_provider"]
    assert portfolio_provider().holdings == []
    assert service.introduced_holdings == ()
    assert service.portfolio is existing
    assert [call.kwargs["target_holding"] for call in
            opening_application.run.call_args_list] == existing.holdings
    loop.run.assert_called_once_with(max_cycles=2)


@pytest.mark.parametrize("restored", [False, True], ids=["adopted", "restored"])
@pytest.mark.parametrize("ready", [False, True], ids=["learning", "ready"])
def test_main_legacy_admission_requires_ready(monkeypatch, restored, ready):
    holding = _holding("A")
    state = _ready(holding) if ready else _learning(holding)
    service, application, factory, _ = _prepare_main(
        monkeypatch, portfolio=Portfolio([holding]), introduced=(),
    )
    main.FileSourceBootstrapStore.return_value.load.return_value = (
        state if restored else None
    )
    application.run.return_value = state

    main.main()

    assert factory.call_args.kwargs["portfolio_provider"]().holdings == (
        [holding] if ready else []
    )
    assert service.introduced_holdings == ()
    assert service.portfolio.holdings == [holding]
    if restored:
        application.run.assert_not_called()
    else:
        application.run.assert_called_once()
        assert application.run.call_args.kwargs["target_holding"] == holding


def test_main_legacy_adoptions_are_sequential_and_failure_isolated(monkeypatch):
    a, b = _holding("A"), _holding("B")
    service, application, factory, _ = _prepare_main(
        monkeypatch, portfolio=Portfolio([a, b]), introduced=(),
    )
    order = []

    def adopt(**kwargs):
        holding = kwargs["target_holding"]
        order.append(holding.symbol)
        if holding == a:
            raise RuntimeError("Opening unavailable")
        return _ready(b)

    application.run.side_effect = adopt
    factory.side_effect = lambda **kwargs: order.append("runtime") or Mock()

    main.main()

    assert factory.call_args.kwargs["portfolio_provider"]().holdings == [b]
    assert order == ["A", "B", "runtime"]
    assert service.introduced_holdings == ()
    assert service.portfolio.holdings == [a, b]


def test_reintroduced_holding_cannot_restore_prior_ready_after_interruption(
    monkeypatch, tmp_path,
):
    holding = _holding("A")
    _, _, factory, _ = _prepare_main(
        monkeypatch, portfolio=Portfolio([holding]), introduced=(),
    )
    truth_path = tmp_path / "truth.json"
    opening_path = tmp_path / "opening"
    FilePortfolioTruthStore(truth_path).save(AcceptedPortfolioTruth(
        positions=(holding,), source_as_of=TIME_ZERO, accepted_at=TIME_ZERO,
    ))
    old_ready = _ready(holding)
    FileSourceBootstrapStore(opening_path).save(old_ready)
    source = Mock()
    services = []

    def service_factory(source_arg, store_arg, clock):
        service = PortfolioTruthService(source_arg, store_arg, clock)
        services.append(service)
        return service

    monkeypatch.setattr(main, "PortfolioTruthService", service_factory)
    monkeypatch.setattr(main, "JsonFilePortfolioSource", Mock(return_value=source))
    monkeypatch.setattr(
        main, "FilePortfolioTruthStore",
        lambda *args: FilePortfolioTruthStore(truth_path),
    )
    monkeypatch.setattr(
        main, "FileSourceBootstrapStore",
        lambda *args: FileSourceBootstrapStore(opening_path),
    )
    identity = Mock()
    identity.resolve.side_effect = KeyboardInterrupt("interrupted before new save")
    research, verification = Mock(), Mock()

    def components(*, portfolio_service, providers):
        store = FileSourceBootstrapStore(opening_path)
        return (
            SourceBootstrapApplication(portfolio_service=portfolio_service, store=store),
            research, identity, verification, store,
        )

    monkeypatch.setattr(main, "_build_opening_components", components)

    def snapshot(positions):
        source.acquire.return_value = PortfolioAcquisitionResult.succeeded(
            CandidatePortfolioSnapshot(
                positions=positions, source_as_of=TIME_ZERO,
                completeness=SnapshotCompleteness.COMPLETE,
            )
        )

    # Full removal is accepted and persisted through the real startup path.
    snapshot(())
    main.main()
    assert FilePortfolioTruthStore(truth_path).load().positions == ()
    assert factory.call_args.kwargs["portfolio_provider"]().holdings == []

    snapshot((holding,))
    with pytest.raises(KeyboardInterrupt, match="interrupted before new save"):
        main.main()
    assert services[-1].introduced_holdings == (holding,)
    assert FilePortfolioTruthStore(truth_path).load().positions == (holding,)
    research.assert_not_called()
    verification.assert_not_called()

    # Recreate services/stores from disk; no new successful Opening can occur.
    identity.resolve.side_effect = RuntimeError("Opening still unavailable")
    main.main()

    assert services[-1].introduced_holdings == ()
    assert services[-1].portfolio.holdings == [holding]
    assert factory.call_args.kwargs["portfolio_provider"]().holdings == [], (
        "Prior membership READY must not admit the reintroduced holding after restart"
    )


def test_local_opening_path_reaches_runtime_eligibility_end_to_end(
    monkeypatch,
    tmp_path,
) -> None:
    a, b, c, d = tuple(_holding(symbol) for symbol in "ABCD")
    source = Mock()
    source.acquire.return_value = PortfolioAcquisitionResult.succeeded(
        CandidatePortfolioSnapshot(
            positions=(a, b, c, d),
            source_as_of=TIME_ZERO,
            completeness=SnapshotCompleteness.COMPLETE,
        )
    )
    truth_store = Mock()
    truth_store.load.return_value = AcceptedPortfolioTruth(
        positions=(a, b),
        source_as_of=TIME_ZERO,
        accepted_at=TIME_ZERO,
    )
    captured = {}

    def portfolio_service_factory(source_arg, store_arg, clock):
        service = PortfolioTruthService(source_arg, store_arg, clock)
        captured["portfolio_service"] = service
        return service

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("AUTONOMOUS_MAX_CYCLES", "2")
    monkeypatch.setenv("OPENAI_MODEL", "test-semantic-model")
    monkeypatch.setenv("LIFEGUARD_PING_URL", "https://example.test/lifeguard")
    monkeypatch.setenv("SEC_USER_AGENT", "test-sec-user-agent")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
    monkeypatch.setattr(main, "JsonFilePortfolioSource", Mock(return_value=source))
    monkeypatch.setattr(
        main,
        "FilePortfolioTruthStore",
        Mock(return_value=truth_store),
    )
    monkeypatch.setattr(main, "PortfolioTruthService", portfolio_service_factory)
    provider_manager = Mock()
    provider_manager.build_named.return_value = {"SEC": Mock()}
    monkeypatch.setattr(main, "ProviderManager", Mock(return_value=provider_manager))
    monkeypatch.setattr(
        main,
        "build_default_source_acquisition_policies",
        Mock(return_value={}),
    )

    opening_store = FileSourceBootstrapStore(tmp_path / "opening-states")
    opening_store.save(_ready(a))
    opening_store.save(_ready(b))
    monkeypatch.setattr(main, "FileSourceBootstrapStore", Mock(return_value=opening_store))
    operation_order = []
    identity_resolver = Mock()

    def resolve_identity(symbol):
        operation_order.append(f"identity:{symbol}")
        return CompanyIdentity(
            ticker=symbol,
            company_name=f"{symbol} Company",
            cik="0000000001",
            exchange="NASDAQ",
        )

    identity_resolver.resolve.side_effect = resolve_identity
    official_url = (
        "https://www.sec.gov/Archives/edgar/data/1/"
        "000000000126000001/report.htm"
    )
    fact = "Cash and cash equivalents were $120 million."

    def research_transport(context):
        operation_order.append(f"research:{context.symbol}")
        if context.symbol == "D":
            return {"candidates": []}
        return {"candidates": [{
            "fact": fact,
            "category": "sec_filing",
            "evidence": [{
                "source_url": official_url,
                "text": "Provider evidence is not authoritative.",
                "locator": "Item 8",
            }],
        }]}

    researcher = BoundedSourceBootstrapResearcher(
        transport=research_transport,
        limits=BoundedResearchLimits(
            max_candidates=10,
            max_document_characters=20_000,
        ),
    )
    event_discovery = Mock(return_value=(Event(
        symbol="C",
        source="SEC",
        title="SEC Filing: 10-K",
        summary="Official annual report",
        published_at="2026-03-30",
        importance=1,
        sentiment="neutral",
        url=official_url,
    ),))
    document_reconstruction = Mock(return_value=SourceDocument(
        source="SEC",
        source_url=official_url,
        title="Sentinel reconstructed report",
        text="Cash and cash equivalents were $120 million.",
    ))
    finding_discovery = Mock(return_value=(SourceFindingCandidate(
        statement=fact,
        evidence=(SourceEvidence(
            source_url=official_url,
            text="Cash and cash equivalents were $120 million",
        ),),
    ),))
    producer = SECSourceBootstrapAcceptanceProducer(
        official_event_discovery=event_discovery,
        document_reconstruction=document_reconstruction,
        finding_discovery=finding_discovery,
    )

    def verify(state):
        operation_order.append(f"verify:{state.request.holding.symbol}")
        return producer(state)

    def build_opening_components(*, portfolio_service, providers):
        return (
            SourceBootstrapApplication(
                portfolio_service=portfolio_service,
                store=opening_store,
            ),
            researcher,
            identity_resolver,
            verify,
            opening_store,
        )

    monkeypatch.setattr(main, "_build_opening_components", build_opening_components)
    runtime_factory = Mock()

    def capture_runtime_factory(**kwargs):
        operation_order.append("runtime_factory")
        captured["portfolio_provider"] = kwargs["portfolio_provider"]
        return Mock()

    runtime_factory.side_effect = capture_runtime_factory
    monkeypatch.setattr(main, "SourceRuntimeFactory", runtime_factory)
    loop = Mock()
    monkeypatch.setattr(main, "build_autonomous_loop", Mock(return_value=loop))

    main.main()

    service = captured["portfolio_service"]
    c_state = opening_store.load(target_holding=c)
    d_state = opening_store.load(target_holding=d)
    runtime_portfolio = captured["portfolio_provider"]()

    assert service.introduced_holdings == (c, d)
    assert operation_order == [
        "identity:C", "research:C", "verify:C",
        "identity:D", "research:D", "verify:D",
        "runtime_factory",
    ]
    assert c_state.verified_identity.ticker == "C"
    assert len(c_state.research_output.candidates) == 1
    assert len(c_state.decisions) == 1
    assert c_state.decisions[0].disposition is OpeningFactDisposition.VERIFIED
    assert c_state.is_ready is True
    assert d_state.is_ready is False
    assert [holding.symbol for holding in runtime_portfolio.holdings] == [
        "A", "B", "C"
    ]
    assert [holding.symbol for holding in service.portfolio.holdings] == [
        "A", "B", "C", "D"
    ]
    event_discovery.assert_called_once_with("C")
    loop.run.assert_called_once_with(max_cycles=2)
