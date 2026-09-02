import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
import requests

from application.source_bootstrap_researcher import (
    BoundedResearchLimits,
    BoundedSourceBootstrapResearcher,
    GroundedResearchContext,
    SourceBootstrapDomainConversionError,
)
from models.company_identity import CompanyIdentity
from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import SourceBootstrapResearchRequest
from modules.perplexity_api_request_client import (
    PerplexityAPIRequestClient,
    PerplexityAPIRequestError,
)
from modules.perplexity_source_bootstrap_transport import (
    PerplexityResearchError,
    PerplexitySourceBootstrapTransport,
)


SENTINELS = (
    "SECRET_KEY",
    "AUTHORIZATION_HEADER",
    "PROMPT_CONTENT",
    "RAW_PROVIDER_BODY",
    "EVIDENCE_CONTENT",
    "SECRET_URL",
    "SECRET_REQUEST_BODY",
    "SECRET_EXCEPTION_MESSAGE",
)


def _context(*, symbol: str = "ONDS") -> GroundedResearchContext:
    return GroundedResearchContext(
        symbol=symbol,
        time_zero=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
        known_identity=CompanyIdentity(
            ticker=symbol,
            company_name="Verified company",
            exchange="NASDAQ",
            cik="0000000001",
        ),
    )


def _client(http_request: Mock) -> PerplexityAPIRequestClient:
    return PerplexityAPIRequestClient(
        api_key="SECRET_KEY",
        http_request=http_request,
        timeout_seconds=12,
        max_output_tokens=1_000,
    )


def _diagnostics(exc: BaseException) -> tuple[object, object, object]:
    return (
        getattr(exc, "category", None),
        getattr(exc, "response_received", None),
        getattr(exc, "status_code", None),
    )


def _assert_safe(exc: BaseException) -> None:
    public_diagnostics = (str(exc),) + _diagnostics(exc)
    exposed = " ".join(str(value) for value in public_diagnostics)
    for sentinel in SENTINELS:
        assert sentinel not in exposed


@pytest.mark.parametrize(
    ("message", "reason"),
    (
        ("research limit exceeded", "RESEARCH_LIMIT_EXCEEDED"),
        ("candidate conversion invalid", "CANDIDATE_INVALID"),
        ("candidate limit exceeded", "CANDIDATE_LIMIT_EXCEEDED"),
    ),
)
def test_domain_conversion_error_classifies_approved_safe_reason(
    message: str,
    reason: str,
) -> None:
    error = SourceBootstrapDomainConversionError(message)

    assert error.category == "DOMAIN_CONVERSION"
    assert error.reason == reason
    assert str(error) == message
    assert error.response_received is None
    assert error.status_code is None


@pytest.mark.parametrize(
    "message",
    (
        "unapproved provider limit exceeded",
        "SECRET_EXCEPTION_MESSAGE",
        "invalid provider enum EVIDENCE_CONTENT",
    ),
)
def test_domain_conversion_error_collapses_unapproved_reason(
    message: str,
) -> None:
    error = SourceBootstrapDomainConversionError(message)

    assert error.category == "DOMAIN_CONVERSION"
    assert error.reason == "DOMAIN_CONVERSION"
    assert str(error) == "grounded research domain conversion failed"


def test_domain_conversion_reason_does_not_leak_provider_value() -> None:
    sentinel = "PROVIDER_DERIVED_SENTINEL"
    error = SourceBootstrapDomainConversionError(
        f"candidate contains {sentinel!r}"
    )

    exposed = " ".join(
        str(value)
        for value in (
            str(error),
            error.category,
            error.reason,
            error.response_received,
            error.status_code,
        )
    )

    assert sentinel not in exposed


@pytest.mark.parametrize(
    ("status_code", "category"),
    (
        (401, "AUTHENTICATION_AUTHORIZATION"),
        (403, "AUTHENTICATION_AUTHORIZATION"),
        (503, "HTTP_STATUS"),
    ),
)
def test_client_preserves_safe_http_diagnostics(
    status_code: int,
    category: str,
) -> None:
    http_request = Mock(return_value=Mock(status_code=status_code))

    with pytest.raises(PerplexityAPIRequestError) as failure:
        _client(http_request)(_context(symbol="PROMPT_CONTENT"))

    assert _diagnostics(failure.value) == (category, True, status_code)
    http_request.assert_called_once()
    _assert_safe(failure.value)


@pytest.mark.parametrize(
    ("transport_error", "category"),
    (
        (
            requests.exceptions.Timeout("SECRET_EXCEPTION_MESSAGE"),
            "TIMEOUT",
        ),
        (
            requests.exceptions.ConnectTimeout(
                "SECRET_EXCEPTION_MESSAGE"
            ),
            "CONNECT_TIMEOUT",
        ),
        (
            requests.exceptions.ReadTimeout(
                "SECRET_EXCEPTION_MESSAGE"
            ),
            "READ_TIMEOUT",
        ),
        (
            requests.exceptions.ConnectionError(
                "SECRET_EXCEPTION_MESSAGE"
            ),
            "NETWORK_ERROR",
        ),
        (
            requests.exceptions.SSLError("SECRET_EXCEPTION_MESSAGE"),
            "NETWORK_ERROR",
        ),
        (OSError("SECRET_EXCEPTION_MESSAGE"), "NETWORK_ERROR"),
    ),
)
def test_client_preserves_safe_network_diagnostics_without_retry(
    transport_error: OSError,
    category: str,
) -> None:
    http_request = Mock(side_effect=transport_error)

    with pytest.raises(PerplexityAPIRequestError) as failure:
        _client(http_request)(_context())

    assert _diagnostics(failure.value) == (
        category,
        False,
        None,
    )
    http_request.assert_called_once()
    _assert_safe(failure.value)


def test_client_classifies_provider_response_parse_failure() -> None:
    response = Mock(status_code=200)
    response.json.side_effect = ValueError("RAW_PROVIDER_BODY")
    http_request = Mock(return_value=response)

    with pytest.raises(PerplexityAPIRequestError) as failure:
        _client(http_request)(_context())

    assert _diagnostics(failure.value) == (
        "PROVIDER_RESPONSE_PARSE",
        True,
        200,
    )
    http_request.assert_called_once()
    _assert_safe(failure.value)


@pytest.mark.parametrize(
    "content",
    (
        "RAW_PROVIDER_BODY",
        json.dumps({"identity": {"company_name": "EVIDENCE_CONTENT"}}),
    ),
)
def test_client_classifies_structured_output_schema_failure(
    content: str,
) -> None:
    response = Mock(status_code=200)
    response.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    http_request = Mock(return_value=response)

    with pytest.raises(PerplexityAPIRequestError) as failure:
        _client(http_request)(_context())

    assert _diagnostics(failure.value) == (
        "STRUCTURED_OUTPUT_SCHEMA",
        True,
        200,
    )
    http_request.assert_called_once()
    _assert_safe(failure.value)


@pytest.mark.parametrize(
    "category",
    (
        "CONNECT_TIMEOUT",
        "READ_TIMEOUT",
        "TIMEOUT",
        "NETWORK_ERROR",
    ),
)
def test_transport_preserves_only_safe_classified_diagnostics(
    category: str,
) -> None:
    source_error = PerplexityAPIRequestError(
        "safe provider failure",
        category=category,
        response_received=False,
        status_code=None,
    )
    provider_request = Mock(side_effect=source_error)
    transport = PerplexitySourceBootstrapTransport(
        provider_request=provider_request
    )

    with pytest.raises(PerplexityResearchError) as failure:
        transport(_context())

    assert _diagnostics(failure.value) == (category, False, None)
    provider_request.assert_called_once()
    _assert_safe(failure.value)


def test_transport_classifies_direct_oserror_as_network_error() -> None:
    provider_request = Mock(
        side_effect=OSError("SECRET_EXCEPTION_MESSAGE")
    )
    transport = PerplexitySourceBootstrapTransport(
        provider_request=provider_request
    )

    with pytest.raises(PerplexityResearchError) as failure:
        transport(_context())

    assert _diagnostics(failure.value) == (
        "NETWORK_ERROR",
        False,
        None,
    )
    provider_request.assert_called_once()
    _assert_safe(failure.value)


def test_transport_does_not_manufacture_timeout_for_unclassified_error(
) -> None:
    source_error = PerplexityAPIRequestError(
        "safe provider failure",
        category=None,
        response_received=False,
        status_code=None,
    )
    provider_request = Mock(side_effect=source_error)
    transport = PerplexitySourceBootstrapTransport(
        provider_request=provider_request
    )

    with pytest.raises(PerplexityResearchError) as failure:
        transport(_context())

    assert _diagnostics(failure.value) == (
        "NETWORK_ERROR",
        False,
        None,
    )
    assert failure.value.category != "NETWORK_TIMEOUT"
    provider_request.assert_called_once()
    _assert_safe(failure.value)


def test_researcher_classifies_domain_conversion_failure() -> None:
    transport = Mock(
        return_value={
            "candidates": [{
                "fact": "EVIDENCE_CONTENT",
                "category": "category",
            }],
        }
    )
    researcher = BoundedSourceBootstrapResearcher(
        transport=transport,
        limits=BoundedResearchLimits(
            max_candidates=1,
            max_document_characters=10_000,
        ),
    )
    request = SourceBootstrapResearchRequest(
        holding=PortfolioHolding(symbol="ONDS", quantity=Decimal("1")),
        time_zero=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError) as failure:
        researcher(
            request,
            known_identity=CompanyIdentity(
                ticker="ONDS",
                company_name="Ondas Holdings Inc.",
                exchange="NASDAQ",
                cik="0001646188",
            ),
        )

    assert getattr(failure.value, "category", None) == "DOMAIN_CONVERSION"
    transport.assert_called_once()
    _assert_safe(failure.value)
