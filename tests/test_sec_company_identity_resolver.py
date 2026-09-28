from datetime import datetime, timezone
from decimal import Decimal
from importlib import import_module
from unittest.mock import Mock

import pytest

from models.company_identity import CompanyIdentity
from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import SourceBootstrapResearchRequest


SEC_TICKERS_URL = (
    "https://www.sec.gov/files/company_tickers_exchange.json"
)
USER_AGENT = "Stock Sentinel test@example.com"


def _resolver_contract():
    try:
        module = import_module("modules.sec_company_identity_resolver")
    except ModuleNotFoundError:
        pytest.fail(
            "official SEC company identity resolver is not implemented"
        )
    return (
        module.SECCompanyIdentityResolver,
        module.SECCompanyIdentityResolutionError,
    )


def _response(payload: object) -> Mock:
    response = Mock()
    response.json.return_value = payload
    return response


def _payload(*, ticker: object = "ONDS", title: object = "Ondas Holdings Inc.",
             cik: object = 1646188) -> dict:
    # Preserve these field-negative cases while reaching association parsing.
    return _association_payload(ticker=ticker, company_name=title, cik=cik)


def _association_payload(
    *,
    ticker: object = "ONDS",
    company_name: object = "Ondas Holdings Inc.",
    cik: object = 1646188,
    exchange: object = "Nasdaq",
) -> dict:
    return {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [[cik, company_name, ticker, exchange]],
    }


def _resolver(http_request: Mock, **overrides):
    resolver_type, _ = _resolver_contract()
    arguments = {
        "user_agent": USER_AGENT,
        "http_request": http_request,
        "timeout_seconds": 17,
    }
    arguments.update(overrides)
    return resolver_type(**arguments)


def _request() -> SourceBootstrapResearchRequest:
    return SourceBootstrapResearchRequest(
        holding=PortfolioHolding(
            symbol="ONDS",
            quantity=Decimal("25"),
        ),
        time_zero=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
    )


def _research_with_official_identity(request, resolver, researcher):
    identity = resolver.resolve(request.holding.symbol)
    return researcher(request, known_identity=identity)


def test_official_sec_entry_resolves_company_identity() -> None:
    http_request = Mock(return_value=_response(_association_payload()))

    identity = _resolver(http_request).resolve("ONDS")

    assert identity == CompanyIdentity(
        ticker="ONDS",
        company_name="Ondas Holdings Inc.",
        cik="0001646188",
        exchange="Nasdaq",
    )


def test_sec_association_record_resolves_complete_opening_identity() -> None:
    http_request = Mock(return_value=_response(_association_payload()))

    identity = _resolver(http_request).resolve("ONDS")

    assert identity == CompanyIdentity(
        ticker="ONDS",
        company_name="Ondas Holdings Inc.",
        cik="0001646188",
        exchange="Nasdaq",
    )


def test_all_opening_identity_fields_come_from_one_association_record() -> None:
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [
            [111, "First Issuer", "FIRST", "NYSE"],
            [222, "Second Issuer", "SECOND", "Nasdaq"],
        ],
    }
    http_request = Mock(return_value=_response(payload))

    identity = _resolver(http_request).resolve("SECOND")

    assert identity == CompanyIdentity(
        ticker="SECOND",
        company_name="Second Issuer",
        cik="0000000222",
        exchange="Nasdaq",
    )


def test_association_record_zero_pads_cik() -> None:
    http_request = Mock(
        return_value=_response(_association_payload(cik=1646188))
    )

    identity = _resolver(http_request).resolve("ONDS")

    assert identity.cik == "0001646188"


@pytest.mark.parametrize("ticker", (None, "", "   "))
def test_association_record_missing_ticker_fails_closed(ticker) -> None:
    _, error_type = _resolver_contract()
    http_request = Mock(
        return_value=_response(_association_payload(ticker=ticker))
    )

    with pytest.raises(error_type):
        _resolver(http_request).resolve("ONDS")


@pytest.mark.parametrize("exchange", (None, "", "   "))
def test_association_record_missing_exchange_fails_closed(exchange) -> None:
    _, error_type = _resolver_contract()
    http_request = Mock(
        return_value=_response(_association_payload(exchange=exchange))
    )

    with pytest.raises(error_type):
        _resolver(http_request).resolve("ONDS")


@pytest.mark.parametrize(
    "payload",
    (
        {"fields": "not-an-array", "data": []},
        {"fields": ["cik", "name", "ticker", "exchange"], "data": {}},
        {"fields": ["cik", "name", "ticker"], "data": []},
        {
            "fields": ["cik", "name", "ticker", "exchange"],
            "data": [[1646188, "Issuer", "ONDS"]],
        },
    ),
)
def test_malformed_sec_association_data_fails_closed(payload: object) -> None:
    _, error_type = _resolver_contract()
    http_request = Mock(return_value=_response(payload))

    with pytest.raises(error_type):
        _resolver(http_request).resolve("ONDS")


def test_association_identity_failure_prevents_research() -> None:
    _, error_type = _resolver_contract()
    resolver = _resolver(
        Mock(return_value=_response(_association_payload(exchange="")))
    )
    researcher = Mock()

    with pytest.raises(error_type):
        _research_with_official_identity(
            _request(),
            resolver,
            researcher,
        )

    researcher.assert_not_called()


def test_resolver_normalizes_ticker_before_lookup() -> None:
    http_request = Mock(return_value=_response(_association_payload()))

    identity = _resolver(http_request).resolve("  onds  ")

    assert identity.ticker == "ONDS"


def test_resolver_zero_pads_numeric_sec_cik() -> None:
    http_request = Mock(
        return_value=_response(_association_payload(cik=1646188))
    )

    identity = _resolver(http_request).resolve("ONDS")

    assert identity.cik == "0001646188"


def test_resolver_lazily_reuses_one_in_memory_mapping() -> None:
    response = _response(_association_payload())
    http_request = Mock(return_value=response)
    resolver = _resolver(http_request)

    first = resolver.resolve("ONDS")
    second = resolver.resolve("onds")

    assert second is first
    http_request.assert_called_once()
    response.raise_for_status.assert_called_once()


def test_resolver_uses_existing_sec_request_contract() -> None:
    http_request = Mock(return_value=_response(_association_payload()))

    _resolver(http_request).resolve("ONDS")

    http_request.assert_called_once_with(
        SEC_TICKERS_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        },
        timeout=17,
    )


@pytest.mark.parametrize("user_agent", (None, "", "   "))
def test_missing_user_agent_fails_before_http_request(user_agent) -> None:
    resolver_type, error_type = _resolver_contract()
    http_request = Mock()

    with pytest.raises(error_type, match="SEC user agent is required"):
        resolver_type(
            user_agent=user_agent,
            http_request=http_request,
            timeout_seconds=17,
        )

    http_request.assert_not_called()


def test_unknown_ticker_fails_closed() -> None:
    _, error_type = _resolver_contract()
    http_request = Mock(return_value=_response(_association_payload()))

    with pytest.raises(
        error_type,
        match="SEC identity was not found for symbol: UNKNOWN",
    ):
        _resolver(http_request).resolve("UNKNOWN")


@pytest.mark.parametrize(
    "payload, error_message",
    (
        ([], "SEC ticker mapping payload is malformed"),
        (_payload(ticker=""), "SEC company ticker is missing"),
        (_payload(ticker="   "), "SEC company ticker is missing"),
        (_payload(title=""), "SEC company title is missing"),
        (_payload(title="   "), "SEC company title is missing"),
        (_payload(cik=None), "SEC company CIK is invalid"),
        (_payload(cik=""), "SEC company CIK is invalid"),
        (_payload(cik="not-a-cik"), "SEC company CIK is invalid"),
    ),
)
def test_malformed_sec_identity_data_fails_closed(payload, error_message) -> None:
    _, error_type = _resolver_contract()
    http_request = Mock(return_value=_response(payload))

    with pytest.raises(error_type, match=error_message):
        _resolver(http_request).resolve("ONDS")


def test_bootstrap_composition_supplies_verified_identity_to_researcher() -> None:
    request = _request()
    identity = CompanyIdentity(
        ticker="ONDS",
        company_name="Ondas Holdings Inc.",
        cik="0001646188",
    )
    resolver = Mock()
    resolver.resolve.return_value = identity
    researcher = Mock(return_value="proposal")

    result = _research_with_official_identity(
        request,
        resolver,
        researcher,
    )

    assert result == "proposal"
    resolver.resolve.assert_called_once_with("ONDS")
    researcher.assert_called_once_with(
        request,
        known_identity=identity,
    )


def test_identity_failure_prevents_research_eligibility() -> None:
    request = _request()
    resolver = Mock()
    resolver.resolve.side_effect = RuntimeError("identity unavailable")
    researcher = Mock()

    with pytest.raises(RuntimeError, match="identity unavailable"):
        _research_with_official_identity(
            request,
            resolver,
            researcher,
        )

    researcher.assert_not_called()


# Synthetic SEC associations, not the unpreserved historical WDS response.
@pytest.mark.parametrize("position", ("before", "after"))
@pytest.mark.parametrize(
    "unrelated_row",
    (
        pytest.param([222, None, "OTHER", "Nasdaq"], id="missing-name"),
        pytest.param([None, "Other Issuer", "OTHER", "Nasdaq"], id="missing-cik"),
        pytest.param([222, "Other Issuer", "OTHER", None], id="missing-exchange"),
    ),
)
def test_valid_target_isolated_from_unrelated_incomplete_identity(
    position, unrelated_row,
) -> None:
    target_row = [111, "WDS Test Issuer", "WDS", "NYSE"]
    rows = ([unrelated_row, target_row] if position == "before"
            else [target_row, unrelated_row])
    payload = {"fields": ["cik", "name", "ticker", "exchange"], "data": rows}
    http_request = Mock(return_value=_response(payload))

    identity = _resolver(http_request).resolve("WDS")

    assert identity == CompanyIdentity(
        ticker="WDS", company_name="WDS Test Issuer",
        cik="0000000111", exchange="NYSE",
    )


@pytest.mark.parametrize(
    "invalid_fields, error_message",
    (
        ({"company_name": None}, "SEC company title is missing"),
        ({"company_name": "   "}, "SEC company title is missing"),
        ({"cik": None}, "SEC company CIK is invalid"),
        ({"cik": "not-a-cik"}, "SEC company CIK is invalid"),
        ({"cik": "12345678901"}, "SEC company CIK is invalid"),
        ({"exchange": None}, "SEC company exchange is missing"),
        ({"exchange": "   "}, "SEC company exchange is missing"),
    ),
)
def test_incomplete_target_still_fails_with_valid_unrelated_association(
    invalid_fields, error_message,
) -> None:
    _, error_type = _resolver_contract()
    payload = _association_payload(ticker="WDS", **invalid_fields)
    payload["data"].insert(0, [222, "Other Issuer", "OTHER", "Nasdaq"])
    http_request = Mock(return_value=_response(payload))

    with pytest.raises(error_type, match=error_message):
        _resolver(http_request).resolve("WDS")


@pytest.mark.parametrize(
    "second_target",
    (
        pytest.param([111, "WDS Test Issuer", "WDS", "NYSE"], id="duplicate"),
        pytest.param([333, "Conflicting Issuer", " wds ", "Nasdaq"], id="conflicting"),
    ),
)
def test_multiple_target_associations_fail_closed(second_target) -> None:
    _, error_type = _resolver_contract()
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [[111, "WDS Test Issuer", "WDS", "NYSE"], second_target],
    }
    http_request = Mock(return_value=_response(payload))

    with pytest.raises(error_type, match="SEC company ticker is ambiguous"):
        _resolver(http_request).resolve("WDS")


@pytest.mark.parametrize(
    "payload, error_message",
    (
        pytest.param(
            {"fields": ["cik", "name", "exchange"],
             "data": [[111, "WDS Test Issuer", "NYSE"]]},
            "SEC ticker mapping payload is malformed", id="no-ticker-column",
        ),
        pytest.param(
            {"fields": ["cik", "name", "ticker", "ticker", "exchange"],
             "data": [[111, "WDS Test Issuer", "WDS", "OTHER", "NYSE"]]},
            "SEC ticker mapping payload is malformed", id="ambiguous-ticker-columns",
        ),
        pytest.param(
            {"fields": ["cik", "name", "ticker", "exchange"],
             "data": [None, [111, "WDS Test Issuer", "WDS", "NYSE"]]},
            "SEC company identity data is malformed", id="unidentifiable-row-before",
        ),
        pytest.param(
            {"fields": ["cik", "name", "ticker", "exchange"],
             "data": [[111, "WDS Test Issuer", "WDS", "NYSE"], []]},
            "SEC company identity data is malformed", id="unidentifiable-row-after",
        ),
    ),
)
def test_unreliable_target_identification_fails_at_structural_boundary(
    payload, error_message,
) -> None:
    _, error_type = _resolver_contract()
    http_request = Mock(return_value=_response(payload))

    with pytest.raises(error_type, match=error_message):
        _resolver(http_request).resolve("WDS")


def test_cached_source_reused_without_validating_unrelated_identities() -> None:
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [
            [111, "WDS Test Issuer", "WDS", "NYSE"],
            [222, "Other Issuer", "OTHER", None],
            [333, "Second Target", "SECOND", "Nasdaq"],
        ],
    }
    response = _response(payload)
    http_request = Mock(return_value=response)
    resolver = _resolver(http_request)
    http_request.assert_not_called()

    first = resolver.resolve("WDS")
    assert first == CompanyIdentity(
        ticker="WDS", company_name="WDS Test Issuer",
        cik="0000000111", exchange="NYSE",
    )
    assert resolver.resolve(" wds ") is first
    assert resolver.resolve("SECOND") == CompanyIdentity(
        ticker="SECOND", company_name="Second Target",
        cik="0000000333", exchange="Nasdaq",
    )
    http_request.assert_called_once()
    response.raise_for_status.assert_called_once()
