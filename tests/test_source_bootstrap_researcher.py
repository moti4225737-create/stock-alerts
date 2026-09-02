from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from application.source_bootstrap_researcher import (
    BoundedResearchLimits,
    BoundedSourceBootstrapResearcher,
    GroundedResearchContext,
    SourceBootstrapDomainConversionError,
)
from models.company_identity import CompanyIdentity
from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import (
    OpeningFactCandidate,
    OpeningResearchResult,
    SourceBootstrapResearchRequest,
)


def _request() -> SourceBootstrapResearchRequest:
    return SourceBootstrapResearchRequest(
        holding=PortfolioHolding(symbol="ONDS", quantity=Decimal("25")),
        time_zero=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
    )


def _identity() -> CompanyIdentity:
    return CompanyIdentity(
        ticker="ONDS",
        company_name="Ondas Holdings Inc.",
        exchange="NASDAQ",
        cik="0001646188",
    )


def _candidate(index: int = 0, *, text: str = "support") -> dict:
    return {
        "fact": f"Opening fact {index}",
        "category": "business",
        "evidence": [{
            "source_url": "https://www.sec.gov/Archives/example",
            "text": text,
            "locator": "Item 1",
        }],
    }


def _researcher(
    transport: Mock,
    *,
    max_candidates: int = 10,
    max_document_characters: int = 1_000,
) -> BoundedSourceBootstrapResearcher:
    return BoundedSourceBootstrapResearcher(
        transport=transport,
        limits=BoundedResearchLimits(
            max_candidates=max_candidates,
            max_document_characters=max_document_characters,
        ),
    )


def test_one_bounded_call_returns_clean_opening_research_result() -> None:
    request = _request()
    identity = _identity()
    transport = Mock(return_value={"candidates": [_candidate()]})

    result = _researcher(transport)(request, known_identity=identity)

    transport.assert_called_once_with(GroundedResearchContext(
        symbol="ONDS", time_zero=request.time_zero, known_identity=identity,
    ))
    assert result == OpeningResearchResult(
        candidates=(OpeningFactCandidate(
            fact="Opening fact 0",
            category="business",
            evidence=result.candidates[0].evidence,
        ),),
        completed_successfully=True,
    )


@pytest.mark.parametrize("count", (0, 3, 10))
def test_zero_to_ten_candidates_are_valid_without_fill_requirement(count: int) -> None:
    transport = Mock(return_value={
        "candidates": [_candidate(index) for index in range(count)],
    })

    result = _researcher(transport)(_request(), known_identity=_identity())

    assert len(result.candidates) == count
    assert result.completed_successfully is True
    transport.assert_called_once()


def test_candidate_specific_bound_fails_closed_without_request_fan_out() -> None:
    transport = Mock(return_value={
        "candidates": [_candidate(index) for index in range(3)],
    })

    with pytest.raises(SourceBootstrapDomainConversionError) as failure:
        _researcher(transport, max_candidates=2)(
            _request(), known_identity=_identity(),
        )

    assert failure.value.reason == "CANDIDATE_LIMIT_EXCEEDED"
    transport.assert_called_once()


def test_candidate_limit_cannot_exceed_approved_maximum_ten() -> None:
    with pytest.raises(ValueError, match="max_candidates must not exceed 10"):
        BoundedResearchLimits(
            max_candidates=11,
            max_document_characters=1_000,
        )


def test_verified_identity_is_required_before_provider_request() -> None:
    transport = Mock()
    researcher = _researcher(transport)

    with pytest.raises(TypeError):
        researcher(_request())

    transport.assert_not_called()


@pytest.mark.parametrize("invalid_result", (
    None,
    [],
    {},
    {"candidates": "not-an-array"},
    {"candidates": [{"fact": "fact", "category": "category"}]},
    {"candidates": [{
        "fact": "fact", "category": "category", "evidence": [],
        "identity": {},
    }]},
))
def test_invalid_candidate_output_has_safe_generic_reason(invalid_result: object) -> None:
    transport = Mock(return_value=invalid_result)

    with pytest.raises(SourceBootstrapDomainConversionError) as failure:
        _researcher(transport)(_request(), known_identity=_identity())

    assert failure.value.category == "DOMAIN_CONVERSION"
    assert failure.value.reason == "CANDIDATE_INVALID"
    transport.assert_called_once()


def test_evidence_character_bound_remains_fail_closed() -> None:
    transport = Mock(return_value={
        "candidates": [_candidate(text="x" * 11)],
    })

    with pytest.raises(SourceBootstrapDomainConversionError) as failure:
        _researcher(transport, max_document_characters=10)(
            _request(), known_identity=_identity(),
        )

    assert failure.value.reason == "RESEARCH_LIMIT_EXCEEDED"
    transport.assert_called_once()


def test_domain_conversion_error_exposes_only_clean_safe_reasons() -> None:
    assert SourceBootstrapDomainConversionError.SAFE_REASONS == {
        "research limit exceeded": "RESEARCH_LIMIT_EXCEEDED",
        "candidate conversion invalid": "CANDIDATE_INVALID",
        "candidate limit exceeded": "CANDIDATE_LIMIT_EXCEEDED",
    }
    assert not hasattr(SourceBootstrapDomainConversionError, "IDENTITY_FIELDS")
