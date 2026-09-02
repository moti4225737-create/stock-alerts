from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from application.source_bootstrap_researcher import (
    BoundedResearchLimits,
    BoundedSourceBootstrapResearcher,
    SourceBootstrapDomainConversionError,
)
from models.company_identity import CompanyIdentity
from models.portfolio_holding import PortfolioHolding
from models.source_evidence import SourceEvidence
import models.source_bootstrap_state as bootstrap_state


def _request():
    return bootstrap_state.SourceBootstrapResearchRequest(
        holding=PortfolioHolding(symbol="ONDS", quantity=Decimal("25")),
        time_zero=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
    )


def _verified_identity() -> CompanyIdentity:
    return CompanyIdentity(
        ticker="ONDS",
        company_name="Ondas Holdings Inc.",
        cik="0001646188",
        exchange="NASDAQ",
    )


def _candidate_payload(index: int = 1) -> dict:
    return {
        "fact": f"Opening fact {index}",
        "category": "sec_filing",
        "evidence": [
            {
                "source_url": f"https://example.test/evidence/{index}",
                "text": f"Evidence text {index}",
                "locator": None,
            }
        ],
    }


def _researcher(transport: Mock) -> BoundedSourceBootstrapResearcher:
    return BoundedSourceBootstrapResearcher(
        transport=transport,
        limits=BoundedResearchLimits(
            max_candidates=10,
            max_document_characters=10_000,
        ),
    )


def _research(candidate_count: int):
    transport = Mock(
        return_value={
            "candidates": [
                _candidate_payload(index)
                for index in range(candidate_count)
            ]
        }
    )
    result = _researcher(transport)(
        _request(),
        known_identity=_verified_identity(),
    )
    transport.assert_called_once()
    return result


@pytest.mark.parametrize("candidate_count", (0, 3))
def test_research_accepts_zero_or_fewer_than_ten_candidates(
    candidate_count: int,
) -> None:
    result = _research(candidate_count)

    assert len(result.candidates) == candidate_count


def test_research_rejects_more_than_ten_candidates_fail_closed() -> None:
    transport = Mock(
        return_value={
            "candidates": [
                _candidate_payload(index) for index in range(11)
            ]
        }
    )

    with pytest.raises(SourceBootstrapDomainConversionError) as failure:
        _researcher(transport)(
            _request(),
            known_identity=_verified_identity(),
        )

    assert failure.value.reason == "CANDIDATE_LIMIT_EXCEEDED"
    transport.assert_called_once()


def test_candidate_contract_is_only_fact_category_and_evidence() -> None:
    candidate = _research(1).candidates[0]

    assert tuple(field.name for field in fields(candidate)) == (
        "fact",
        "category",
        "evidence",
    )


def test_provider_result_does_not_repeat_or_authorize_identity() -> None:
    result = _research(1)

    assert not hasattr(result, "identity")
    assert result.candidates[0].fact == "Opening fact 0"


def test_provider_cannot_fill_or_modify_authoritative_opening_identity() -> None:
    provider_identity = {
        "ticker": "PROVIDER_TICKER",
        "company_name": "Provider company",
        "cik": "9999999999",
        "exchange": "Provider exchange",
    }
    transport = Mock(
        return_value={
            "candidates": [_candidate_payload()],
            "identity": provider_identity,
        }
    )

    with pytest.raises(SourceBootstrapDomainConversionError) as failure:
        _researcher(transport)(
            _request(),
            known_identity=_verified_identity(),
        )

    assert failure.value.reason == "CANDIDATE_INVALID"
    transport.assert_called_once()


def test_disposition_contract_contains_exactly_three_sentinel_outcomes(
) -> None:
    disposition = bootstrap_state.OpeningFactDisposition

    assert {value.value for value in disposition} == {
        "verified",
        "rejected",
        "unresolved",
    }


def _opening_state(
    *,
    dispositions: tuple[str, ...],
    identity: CompanyIdentity | None = None,
    completed_successfully: bool = True,
):
    candidate_type = bootstrap_state.OpeningFactCandidate
    decision_type = bootstrap_state.OpeningFactDecision
    disposition_type = bootstrap_state.OpeningFactDisposition
    research_type = bootstrap_state.OpeningResearchResult

    candidates = tuple(
        candidate_type(
            fact=f"Opening fact {index}",
            category="sec_filing",
            evidence=(
                SourceEvidence(
                    source_url=f"https://example.test/evidence/{index}",
                    text=f"Evidence text {index}",
                ),
            ),
        )
        for index, _ in enumerate(dispositions)
    )
    decisions = tuple(
        decision_type(
            candidate=candidate,
            disposition=disposition_type(disposition),
        )
        for candidate, disposition in zip(candidates, dispositions)
    )
    return bootstrap_state.SourceBootstrapState(
        request=_request(),
        verified_identity=identity or _verified_identity(),
        research_output=research_type(
            candidates=candidates,
            completed_successfully=completed_successfully,
        ),
        decisions=decisions,
    )


@pytest.mark.parametrize(
    "dispositions",
    (
        (),
        ("rejected",),
        ("unresolved",),
        ("rejected", "unresolved"),
    ),
)
def test_ready_requires_at_least_one_verified_fact(
    dispositions: tuple[str, ...],
) -> None:
    state = _opening_state(dispositions=dispositions)

    assert state.lifecycle is bootstrap_state.SourceBootstrapLifecycle.LEARNING
    assert not state.is_ready


@pytest.mark.parametrize(
    ("identity", "completed_successfully"),
    (
        (
            CompanyIdentity(
                ticker="ONDS",
                company_name="Ondas Holdings Inc.",
                cik="0001646188",
                exchange=None,
            ),
            True,
        ),
        (_verified_identity(), False),
    ),
)
def test_ready_requires_complete_identity_and_successful_research(
    identity: CompanyIdentity,
    completed_successfully: bool,
) -> None:
    state = _opening_state(
        dispositions=("verified",),
        identity=identity,
        completed_successfully=completed_successfully,
    )

    assert state.lifecycle is bootstrap_state.SourceBootstrapLifecycle.LEARNING
    assert not state.is_ready


def test_ready_with_complete_identity_successful_research_and_all_dispositions(
) -> None:
    state = _opening_state(
        dispositions=("verified", "rejected", "unresolved"),
    )

    assert state.lifecycle is bootstrap_state.SourceBootstrapLifecycle.READY
    assert state.is_ready


def test_materiality_is_not_part_of_candidate_decision_or_ready_contract(
) -> None:
    state = _opening_state(dispositions=("verified",))

    candidate = state.research_output.candidates[0]
    decision = state.decisions[0]
    assert not hasattr(candidate, "material")
    assert not hasattr(decision, "material")
    assert state.is_ready
