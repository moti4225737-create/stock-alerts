from dataclasses import fields
import json
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


def test_real_client_metadata_crosses_transport_without_entering_domain():
    from modules.perplexity_api_request_client import PerplexityAPIRequestClient

    payload = _provider_result(evidence_text="Official evidence")
    response = Mock(status_code=200)
    response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(payload)}}],
        "usage": {"total_tokens": 100},
        "citations": ["https://example.test/evidence"],
        "search_results": [],
    }
    http = Mock(return_value=response)
    client = PerplexityAPIRequestClient(
        api_key="unit-test", http_request=http,
        timeout_seconds=60, max_output_tokens=2000,
    )
    received = []

    def request(context):
        result = client(context)
        received.append(result)
        return result

    result = _researcher(request)(_request(), known_identity=_identity())
    assert result.completed_successfully
    assert len(result.candidates) == 1
    assert received[0]["_operational_evidence"] == {"usage": {"total_tokens": 100}}
    assert "_provider_metadata" in received[0]
    http.assert_called_once()


def test_transport_does_not_hide_unknown_domain_fields_with_metadata():
    payload = _provider_result(evidence_text="evidence")
    payload.update(_operational_evidence={}, _provider_metadata={}, ready=True)
    with pytest.raises(ValueError, match="candidate conversion invalid"):
        _researcher(Mock(return_value=payload))(_request(), known_identity=_identity())
