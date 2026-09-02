from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from application.source_bootstrap_researcher import (
    BoundedResearchLimits,
    BoundedSourceBootstrapResearcher,
    GroundedResearchContext,
)
from models.company_identity import CompanyIdentity
from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import SourceBootstrapResearchRequest
from modules.perplexity_source_bootstrap_transport import (
    PerplexityResearchError,
    PerplexitySourceBootstrapTransport,
)


def _request() -> SourceBootstrapResearchRequest:
    return SourceBootstrapResearchRequest(
        holding=PortfolioHolding(
            symbol="ONDS",
            quantity=Decimal("25"),
        ),
        time_zero=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
    )


def _identity() -> CompanyIdentity:
    return CompanyIdentity(
        ticker="ONDS",
        company_name="Ondas Holdings Inc.",
        exchange="NASDAQ",
        cik="0001646188",
    )


def _provider_result(*, evidence_text: str) -> dict:
    return {
        "candidates": [{
            "fact": "ONDS develops autonomous drone systems.",
            "category": "sec_filing",
            "evidence": [{
                "source_url": "https://sec.example/onds-10k",
                "text": evidence_text,
                "locator": "Item 1 - Business",
            }],
        }],
    }


def _researcher(provider_request: Mock) -> BoundedSourceBootstrapResearcher:
    return BoundedSourceBootstrapResearcher(
        transport=PerplexitySourceBootstrapTransport(
            provider_request=provider_request,
        ),
        limits=BoundedResearchLimits(
            max_candidates=2,
            max_document_characters=1_000,
        ),
    )


def test_perplexity_transport_makes_one_request_with_only_bootstrap_context(
) -> None:
    request = _request()
    identity = _identity()
    result = _provider_result(
        evidence_text="We develop autonomous drone systems."
    )
    provider_request = Mock(return_value=result)

    proposal = _researcher(provider_request)(
        request,
        known_identity=identity,
    )

    provider_request.assert_called_once_with(
        GroundedResearchContext(
            symbol="ONDS",
            time_zero=request.time_zero,
            known_identity=identity,
        )
    )
    assert tuple(field.name for field in fields(GroundedResearchContext)) == (
        "symbol",
        "time_zero",
        "known_identity",
    )
    evidence = proposal.candidates[0].evidence[0]
    assert evidence.source_url == "https://sec.example/onds-10k"
    assert evidence.text == "We develop autonomous drone systems."
    assert evidence.locator == "Item 1 - Business"


def test_perplexity_ready_claim_cannot_bypass_sentinel_validation() -> None:
    request = _request()
    result = _provider_result(
        evidence_text="This evidence is absent from the document."
    )
    result["candidates"][0]["disposition"] = "verified"
    provider_request = Mock(return_value=result)

    with pytest.raises(ValueError, match="candidate conversion invalid"):
        _researcher(provider_request)(
            request,
            known_identity=_identity(),
        )

    provider_request.assert_called_once()


def test_perplexity_malformed_or_oversized_output_fails_without_fan_out(
) -> None:
    result = _provider_result(
        evidence_text="We develop autonomous drone systems."
    )
    result["candidates"] *= 3
    provider_request = Mock(return_value=result)

    with pytest.raises(ValueError, match="candidate limit exceeded"):
        _researcher(provider_request)(
            _request(),
            known_identity=_identity(),
        )

    provider_request.assert_called_once()


def test_perplexity_provider_failure_is_explicit_and_has_no_retry() -> None:
    provider_request = Mock(side_effect=OSError("provider unavailable"))

    with pytest.raises(
        PerplexityResearchError,
        match="Perplexity research request failed",
    ):
        _researcher(provider_request)(
            _request(),
            known_identity=_identity(),
        )

    provider_request.assert_called_once()
