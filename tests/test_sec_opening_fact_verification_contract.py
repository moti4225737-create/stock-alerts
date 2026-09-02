from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from application.sec_source_bootstrap_acceptance_producer import (
    SECSourceBootstrapAcceptanceProducer,
)
from models.company_identity import CompanyIdentity
from models.event import Event
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
from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate


CIK = "0001646188"
OFFICIAL_URL = (
    "https://www.sec.gov/Archives/edgar/data/1646188/"
    "000164618826000001/onds-20251231.htm"
)
FACT = "Cash and cash equivalents were $120 million."
RECONSTRUCTED_EVIDENCE = "Cash and cash equivalents were $120 million"


def _identity(*, exchange: str | None = "Nasdaq") -> CompanyIdentity:
    return CompanyIdentity(
        ticker="ONDS",
        company_name="Ondas Holdings Inc.",
        cik=CIK,
        exchange=exchange,
    )


def _candidate(
    *,
    fact: str = FACT,
    category: str = "sec_filing",
    source_url: str = OFFICIAL_URL,
) -> OpeningFactCandidate:
    return OpeningFactCandidate(
        fact=fact,
        category=category,
        evidence=(
            SourceEvidence(
                source_url=source_url,
                text="Provider-supplied evidence is not authoritative.",
            ),
        ),
    )


def _state(
    *candidates: OpeningFactCandidate,
    identity: CompanyIdentity | None = None,
) -> SourceBootstrapState:
    return SourceBootstrapState(
        request=SourceBootstrapResearchRequest(
            holding=PortfolioHolding(
                symbol="ONDS",
                quantity=Decimal("25"),
            ),
            time_zero=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
        ),
        verified_identity=identity if identity is not None else _identity(),
        research_output=OpeningResearchResult(
            candidates=tuple(candidates),
            completed_successfully=True,
        ),
    )


def _event(
    *,
    symbol: str = "ONDS",
    source: str = "SEC",
    url: str = OFFICIAL_URL,
) -> Event:
    return Event(
        symbol=symbol,
        source=source,
        title="SEC Filing: 10-K",
        summary="Official annual report",
        published_at="2026-03-30",
        importance=1,
        sentiment="neutral",
        url=url,
    )


def _document(*, source_url: str = OFFICIAL_URL) -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url=source_url,
        title="Sentinel-reconstructed annual report",
        text=f"{RECONSTRUCTED_EVIDENCE}.",
    )


def _finding(
    *,
    statement: str = FACT,
    source_url: str = OFFICIAL_URL,
) -> SourceFindingCandidate:
    return SourceFindingCandidate(
        statement=statement,
        evidence=(
            SourceEvidence(
                source_url=source_url,
                text=RECONSTRUCTED_EVIDENCE,
            ),
        ),
    )


def _dependencies(
    *,
    events: tuple[Event, ...] = (_event(),),
    document: SourceDocument | None = None,
    findings: tuple[SourceFindingCandidate, ...] | None = None,
) -> tuple[Mock, Mock, Mock]:
    event_discovery = Mock(return_value=events)
    document_reconstruction = Mock(
        return_value=document if document is not None else _document()
    )
    finding_discovery = Mock(
        return_value=findings if findings is not None else (_finding(),)
    )
    return event_discovery, document_reconstruction, finding_discovery


def _producer(
    dependencies: tuple[Mock, Mock, Mock],
    *,
    budget: int | None = None,
) -> SECSourceBootstrapAcceptanceProducer:
    event_discovery, document_reconstruction, finding_discovery = dependencies
    return SECSourceBootstrapAcceptanceProducer(
        official_event_discovery=event_discovery,
        document_reconstruction=document_reconstruction,
        finding_discovery=finding_discovery,
        max_distinct_verification_targets=budget,
    )


def _assert_one_decision(
    output: object,
    candidate: OpeningFactCandidate,
    disposition: OpeningFactDisposition,
) -> OpeningFactDecision:
    assert isinstance(output, tuple)
    assert len(output) == 1
    decision = output[0]
    assert isinstance(decision, OpeningFactDecision)
    assert decision.candidate is candidate
    assert decision.disposition is disposition
    assert tuple(decision.__dataclass_fields__) == ("candidate", "disposition")
    return decision


def test_sec_opening_candidate_is_verified_from_reconstructed_truth() -> None:
    candidate = _candidate()
    dependencies = _dependencies()

    output = _producer(dependencies)(_state(candidate))

    _assert_one_decision(output, candidate, OpeningFactDisposition.VERIFIED)
    event_discovery, document_reconstruction, finding_discovery = dependencies
    event_discovery.assert_called_once_with("ONDS")
    document_reconstruction.assert_called_once_with(_event())
    finding_discovery.assert_called_once_with(_document())
    assert candidate.evidence[0].text not in _document().text


@pytest.mark.parametrize("identity", (None, _identity(exchange=None)))
def test_incomplete_verified_identity_is_unresolved_without_sec_work(
    identity: CompanyIdentity | None,
) -> None:
    candidate = _candidate()
    dependencies = _dependencies()
    state = _state(candidate)
    state = replace(state, verified_identity=identity)

    output = _producer(dependencies)(state)

    _assert_one_decision(output, candidate, OpeningFactDisposition.UNRESOLVED)
    for dependency in dependencies:
        dependency.assert_not_called()


def test_unsupported_candidate_is_unresolved_without_sec_work() -> None:
    candidate = _candidate(category="fda_recall")
    dependencies = _dependencies()

    output = _producer(dependencies)(_state(candidate))

    _assert_one_decision(output, candidate, OpeningFactDisposition.UNRESOLVED)
    for dependency in dependencies:
        dependency.assert_not_called()


def test_noncanonical_sec_evidence_is_unresolved_before_reconstruction() -> None:
    candidate = _candidate(source_url="https://sec.example/not-official")
    dependencies = _dependencies()

    output = _producer(dependencies)(_state(candidate))

    _assert_one_decision(output, candidate, OpeningFactDisposition.UNRESOLVED)
    dependencies[1].assert_not_called()
    dependencies[2].assert_not_called()


@pytest.mark.parametrize(
    "event",
    (
        _event(symbol="OTHER"),
        _event(source="FDA"),
        _event(url=OFFICIAL_URL.replace("/data/1646188/", "/data/320193/")),
    ),
)
def test_identity_or_event_mismatch_is_unresolved(event: Event) -> None:
    candidate = _candidate(source_url=event.url)
    dependencies = _dependencies(events=(event,))

    output = _producer(dependencies)(_state(candidate))

    _assert_one_decision(output, candidate, OpeningFactDisposition.UNRESOLVED)
    dependencies[1].assert_not_called()
    dependencies[2].assert_not_called()


@pytest.mark.parametrize(
    "findings",
    ((), (_finding(statement="A different fact."),)),
)
def test_absent_or_nonmatching_reconstructed_finding_is_unresolved(
    findings: tuple[SourceFindingCandidate, ...],
) -> None:
    candidate = _candidate()
    dependencies = _dependencies(findings=findings)

    output = _producer(dependencies)(_state(candidate))

    decision = _assert_one_decision(
        output,
        candidate,
        OpeningFactDisposition.UNRESOLVED,
    )
    assert decision.disposition is not OpeningFactDisposition.REJECTED


def test_duplicate_opening_targets_verify_once_and_keep_each_decision() -> None:
    first = _candidate()
    second = _candidate()
    dependencies = _dependencies()

    output = _producer(dependencies)(_state(first, second))

    assert isinstance(output, tuple)
    assert [decision.candidate for decision in output] == [first, second]
    assert all(
        decision.disposition is OpeningFactDisposition.VERIFIED
        for decision in output
    )
    for dependency in dependencies:
        dependency.assert_called_once()


def test_opening_verification_budget_makes_excess_target_unresolved() -> None:
    first = _candidate()
    second_url = OFFICIAL_URL.replace(".htm", "-exhibit.htm")
    second = _candidate(fact="A second fact.", source_url=second_url)
    dependencies = _dependencies()

    output = _producer(dependencies, budget=1)(_state(first, second))

    assert isinstance(output, tuple)
    assert [decision.disposition for decision in output] == [
        OpeningFactDisposition.VERIFIED,
        OpeningFactDisposition.UNRESOLVED,
    ]
    for dependency in dependencies:
        dependency.assert_called_once()


def test_verified_decision_can_complete_opening_ready_handoff() -> None:
    candidate = _candidate()
    state = _state(candidate)
    output = _producer(_dependencies())(state)

    completed = replace(state, decisions=output)

    assert completed.lifecycle is SourceBootstrapLifecycle.READY
    assert completed.is_ready
