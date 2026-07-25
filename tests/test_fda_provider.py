from unittest.mock import Mock

import requests

from models.company_identity import CompanyIdentity
from models.event import Event
from modules.data_provider import DataProvider
from modules.fda_provider import FDAProvider


def build_provider(
    identity: CompanyIdentity | None,
    records: list[dict] | None = None,
    max_events: int = 10,
) -> tuple[FDAProvider, Mock, Mock]:
    ticker_resolver = Mock()
    ticker_resolver.get_company_identity.return_value = identity

    client = Mock()
    client.search_drug_enforcement.return_value = records or []

    provider = FDAProvider(
        client=client,
        ticker_resolver=ticker_resolver,
        max_events=max_events,
    )

    return provider, ticker_resolver, client


def test_provider_inherits_from_data_provider() -> None:
    provider, _, _ = build_provider(identity=None)

    assert isinstance(provider, DataProvider)


def test_fetch_events_returns_empty_list_for_empty_symbol() -> None:
    provider, ticker_resolver, client = build_provider(
        identity=None
    )

    events = provider.fetch_events("   ")

    assert events == []
    ticker_resolver.get_company_identity.assert_not_called()
    client.search_drug_enforcement.assert_not_called()


def test_fetch_events_returns_empty_list_when_identity_is_missing() -> None:
    provider, ticker_resolver, client = build_provider(
        identity=None
    )

    events = provider.fetch_events("lqda")

    assert events == []
    ticker_resolver.get_company_identity.assert_called_once_with(
        "LQDA"
    )
    client.search_drug_enforcement.assert_not_called()


def test_fetch_events_builds_query_from_company_name() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    provider, ticker_resolver, client = build_provider(
        identity=identity
    )

    events = provider.fetch_events("  lqda  ")

    assert events == []
    ticker_resolver.get_company_identity.assert_called_once_with(
        "LQDA"
    )
    client.search_drug_enforcement.assert_called_once_with(
        query='recalling_firm:"Liquidia"',
        limit=10,
    )


def test_fetch_events_converts_recall_record_to_event() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    records = [
        {
            "recalling_firm": "Liquidia Technologies",
            "reason_for_recall": "Example recall reason",
            "product_description": "Example drug product",
            "recall_number": "D-1234-2026",
            "classification": "Class II",
            "status": "Ongoing",
            "report_date": "20260720",
        }
    ]

    provider, _, client = build_provider(
        identity=identity,
        records=records,
    )

    events = provider.fetch_events("LQDA")

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, Event)
    assert event.symbol == "LQDA"
    assert event.source == "FDA"
    assert event.title == (
        "FDA Drug Recall — Class II — Liquidia Technologies"
    )
    assert event.summary == (
        "Example recall reason"
        " | Product: Example drug product"
        " | Recall number: D-1234-2026"
        " | Status: Ongoing"
    )
    assert event.published_at == "20260720"
    assert event.importance == 1
    assert event.sentiment == "negative"
    assert event.url == (
        "https://www.accessdata.fda.gov/scripts/ires/index.cfm"
    )

    client.search_drug_enforcement.assert_called_once_with(
        query='recalling_firm:"Liquidia"',
        limit=10,
    )


def test_fetch_events_uses_initiation_date_when_report_date_missing() -> None:
    identity = CompanyIdentity(
        ticker="TEST",
        company_name="Example Inc.",
    )

    records = [
        {
            "recalling_firm": "Example",
            "reason_for_recall": "Example reason",
            "recall_initiation_date": "20260701",
        }
    ]

    provider, _, _ = build_provider(
        identity=identity,
        records=records,
    )

    events = provider.fetch_events("TEST")

    assert len(events) == 1
    assert events[0].published_at == "20260701"


def test_fetch_events_skips_unusable_records() -> None:
    identity = CompanyIdentity(
        ticker="TEST",
        company_name="Example Ltd",
    )

    records = [
        {},
        {
            "recalling_firm": "   ",
            "reason_for_recall": None,
        },
        {
            "reason_for_recall": "Valid reason",
        },
    ]

    provider, _, _ = build_provider(
        identity=identity,
        records=records,
    )

    events = provider.fetch_events("TEST")

    assert len(events) == 1
    assert events[0].summary == "Valid reason"


def test_fetch_events_returns_empty_list_on_request_error() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    provider, _, client = build_provider(identity=identity)
    client.search_drug_enforcement.side_effect = (
        requests.RequestException("Network failure")
    )

    events = provider.fetch_events("LQDA")

    assert events == []


def test_fetch_events_passes_custom_max_events() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    provider, _, client = build_provider(
        identity=identity,
        max_events=3,
    )

    provider.fetch_events("LQDA")

    client.search_drug_enforcement.assert_called_once_with(
        query='recalling_firm:"Liquidia"',
        limit=3,
    )


def test_provider_rejects_invalid_max_events() -> None:
    try:
        FDAProvider(max_events=0)
    except ValueError as error:
        assert str(error) == "max_events must be at least 1"
    else:
        raise AssertionError(
            "Expected ValueError for max_events below 1."
        )


if __name__ == "__main__":
    test_provider_inherits_from_data_provider()
    test_fetch_events_returns_empty_list_for_empty_symbol()
    test_fetch_events_returns_empty_list_when_identity_is_missing()
    test_fetch_events_builds_query_from_company_name()
    test_fetch_events_converts_recall_record_to_event()
    test_fetch_events_uses_initiation_date_when_report_date_missing()
    test_fetch_events_skips_unusable_records()
    test_fetch_events_returns_empty_list_on_request_error()
    test_fetch_events_passes_custom_max_events()
    test_provider_rejects_invalid_max_events()

    print("FDAProvider tests passed.")