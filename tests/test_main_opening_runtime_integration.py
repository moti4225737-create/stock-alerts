from datetime import datetime, timezone
from unittest.mock import Mock

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


TIME_ZERO = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)


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
    loop.run.assert_called_once_with()


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


def test_main_zero_introductions_preserves_existing_runtime_behavior(
    monkeypatch,
) -> None:
    existing = Portfolio([_holding("A"), _holding("B")])
    _, opening_application, runtime_factory, loop = _prepare_main(
        monkeypatch,
        portfolio=existing,
        introduced=(),
    )

    main.main()

    opening_application.run.assert_not_called()
    portfolio_provider = runtime_factory.call_args.kwargs["portfolio_provider"]
    assert portfolio_provider() is existing
    loop.run.assert_called_once_with()


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
    loop.run.assert_called_once_with()
