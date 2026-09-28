from unittest.mock import Mock
from datetime import datetime, timezone

import pytest

import requests

from models.company_identity import CompanyIdentity
from models.event import Event
from modules.data_provider import DataProvider
from modules.fda_provider import FDAProvider
from modules.ticker_resolver import TickerResolver


def _g1_fda(records, store):
    resolver = Mock()
    resolver.get_company_identity.return_value = CompanyIdentity(ticker="TEST", company_name="Test")
    resolver.prepare_company_search_name.return_value = "Test"
    client = Mock()
    client.search_drug_enforcement.return_value = records
    return FDAProvider(client=client, ticker_resolver=resolver,
        source_observation_store=store,
        time_zero_for=lambda symbol: datetime(2026, 7, 20, 12, tzinfo=timezone.utc))


def _g1_recall(number="D-0001-2026", occurrence="20260721"):
    return {"recall_number": number, "recalling_firm": "Test",
        "reason_for_recall": "Contamination", "classification": "Class II",
        "report_date": occurrence, "recall_initiation_date": occurrence}


@pytest.mark.parametrize("occurrence,live", [
    ("20260719", False), ("20260721", True), (None, False), ("invalid", False),
])
def test_g1_fda_late_discovery_uses_source_time_and_persists_observation(occurrence, live):
    store = Mock()
    store.load.return_value = None
    events = _g1_fda([_g1_recall(occurrence=occurrence)], store).fetch_events("TEST")
    assert len(events) == int(live), "Unseen historical/undated recalls are not NEW"
    assert store.save.called, "Recall acquisition must reach Source Observation"
    state = store.save.call_args.args[0]
    assert state.objects
    assert len(state.pending) == int(live)
    if live:
        assert events[0].event_id
        assert state.pending[0]["event_id"] == events[0].event_id


def test_g2_fda_distinct_recalls_have_distinct_stable_ids():
    store = Mock()
    store.load.return_value = None
    events = _g1_fda([_g1_recall("D-0001-2026"), _g1_recall("D-0002-2026")], store).fetch_events("TEST")
    assert len(events) == 2
    assert all(event.event_id for event in events), "Source occurrence IDs must be explicit"
    assert events[0].event_id != events[1].event_id


def test_g2_fda_restart_preserves_same_recall_identity():
    store = Mock()
    store.load.return_value = None
    first = _g1_fda([_g1_recall()], store).fetch_events("TEST")[0]
    if store.save.called:
        store.load.return_value = store.save.call_args.args[0]
    replay = _g1_fda([_g1_recall()], store).fetch_events("TEST")[0]
    assert first.event_id, "A replayable recall requires a source occurrence ID"
    assert replay.event_id == first.event_id


def build_provider(
    identity: CompanyIdentity | None,
    records: list[dict] | None = None,
    max_events: int = 10,
) -> tuple[FDAProvider, Mock, Mock]:
    ticker_resolver = Mock()
    ticker_resolver.get_company_identity.return_value = identity

    if identity is not None:
        prepared_name = TickerResolver.prepare_company_search_name(
            identity.company_name
        )
        ticker_resolver.prepare_company_search_name.return_value = (
            prepared_name
        )

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
    ticker_resolver.prepare_company_search_name.assert_not_called()
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
    ticker_resolver.prepare_company_search_name.assert_not_called()
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
    ticker_resolver.prepare_company_search_name.assert_called_once_with(
        "Liquidia Corp"
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


def test_fetch_events_propagates_request_error() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    provider, _, client = build_provider(identity=identity)
    client.search_drug_enforcement.side_effect = (
        requests.RequestException("Network failure")
    )

    with pytest.raises(requests.RequestException, match="Network failure"):
        provider.fetch_events("LQDA")


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
    test_fetch_events_propagates_request_error()
    test_fetch_events_passes_custom_max_events()
    test_provider_rejects_invalid_max_events()

    print("FDAProvider tests passed.")
