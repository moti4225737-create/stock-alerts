from unittest.mock import Mock

import requests

from models.company_identity import CompanyIdentity
from models.event import Event
from modules.clinical_trials_provider import (
    ClinicalTrialsProvider,
)
from modules.data_provider import DataProvider


def build_provider(
    identity: CompanyIdentity | None,
    studies: list[dict] | None = None,
    max_events: int = 10,
) -> tuple[ClinicalTrialsProvider, Mock, Mock]:
    ticker_resolver = Mock()
    ticker_resolver.get_company_identity.return_value = identity

    if identity is not None:
        ticker_resolver.prepare_company_search_name.return_value = (
            identity.company_name
        )

    client = Mock()
    client.search_studies.return_value = studies or []

    provider = ClinicalTrialsProvider(
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
    client.search_studies.assert_not_called()


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
    client.search_studies.assert_not_called()


def test_fetch_events_uses_prepared_company_name() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    provider, ticker_resolver, client = build_provider(
        identity=identity
    )

    ticker_resolver.prepare_company_search_name.return_value = (
        "Liquidia"
    )

    events = provider.fetch_events("  lqda  ")

    assert events == []

    ticker_resolver.get_company_identity.assert_called_once_with(
        "LQDA"
    )
    ticker_resolver.prepare_company_search_name.assert_called_once_with(
        "Liquidia Corp"
    )
    client.search_studies.assert_called_once_with(
        query="Liquidia",
        page_size=10,
    )


def test_fetch_events_returns_empty_list_for_empty_search_name() -> None:
    identity = CompanyIdentity(
        ticker="TEST",
        company_name="Example Inc.",
    )

    provider, ticker_resolver, client = build_provider(
        identity=identity
    )

    ticker_resolver.prepare_company_search_name.return_value = ""

    events = provider.fetch_events("TEST")

    assert events == []
    ticker_resolver.prepare_company_search_name.assert_called_once_with(
        "Example Inc."
    )
    client.search_studies.assert_not_called()


def test_fetch_events_converts_study_to_event() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    studies = [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT01234567",
                    "briefTitle": (
                        "A Study of Yutrepia in Participants "
                        "With Pulmonary Hypertension"
                    ),
                },
                "statusModule": {
                    "overallStatus": "RECRUITING",
                    "studyFirstPostDateStruct": {
                        "date": "2026-07-20"
                    },
                },
                "conditionsModule": {
                    "conditions": [
                        "Pulmonary Hypertension",
                        "Interstitial Lung Disease",
                    ]
                },
                "descriptionModule": {
                    "briefSummary": (
                        "This study evaluates the safety and "
                        "effectiveness of Yutrepia."
                    )
                },
            }
        }
    ]

    provider, ticker_resolver, client = build_provider(
        identity=identity,
        studies=studies,
    )

    ticker_resolver.prepare_company_search_name.return_value = (
        "Liquidia"
    )

    events = provider.fetch_events("LQDA")

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, Event)
    assert event.symbol == "LQDA"
    assert event.source == "ClinicalTrials.gov"
    assert event.title == (
        "Clinical Trial — A Study of Yutrepia in Participants "
        "With Pulmonary Hypertension"
    )
    assert event.summary == (
        "This study evaluates the safety and effectiveness "
        "of Yutrepia."
        " | NCT ID: NCT01234567"
        " | Status: RECRUITING"
        " | Conditions: Pulmonary Hypertension, "
        "Interstitial Lung Disease"
    )
    assert event.published_at == "2026-07-20"
    assert event.importance == 2
    assert event.sentiment == "neutral"
    assert event.url == (
        "https://clinicaltrials.gov/study/NCT01234567"
    )

    client.search_studies.assert_called_once_with(
        query="Liquidia",
        page_size=10,
    )


def test_fetch_events_uses_start_date_when_post_date_missing() -> None:
    identity = CompanyIdentity(
        ticker="TEST",
        company_name="Example Inc.",
    )

    studies = [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT07654321",
                    "briefTitle": "Example Clinical Study",
                },
                "statusModule": {
                    "overallStatus": "ACTIVE_NOT_RECRUITING",
                    "startDateStruct": {
                        "date": "2026-06"
                    },
                },
            }
        }
    ]

    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=studies,
    )

    ticker_resolver.prepare_company_search_name.return_value = (
        "Example"
    )

    events = provider.fetch_events("TEST")

    assert len(events) == 1
    assert events[0].published_at == "2026-06"


def test_fetch_events_skips_studies_without_required_fields() -> None:
    identity = CompanyIdentity(
        ticker="TEST",
        company_name="Example Ltd",
    )

    studies = [
        {},
        {
            "protocolSection": {},
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000001",
                }
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "briefTitle": "Study Without NCT ID",
                }
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000002",
                    "briefTitle": "Valid Example Study",
                },
                "statusModule": {
                    "overallStatus": "COMPLETED",
                },
            }
        },
    ]

    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=studies,
    )

    ticker_resolver.prepare_company_search_name.return_value = (
        "Example"
    )

    events = provider.fetch_events("TEST")

    assert len(events) == 1
    assert events[0].title == (
        "Clinical Trial — Valid Example Study"
    )
    assert events[0].url == (
        "https://clinicaltrials.gov/study/NCT00000002"
    )


def test_fetch_events_builds_summary_without_optional_fields() -> None:
    identity = CompanyIdentity(
        ticker="TEST",
        company_name="Example Ltd",
    )

    studies = [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000003",
                    "briefTitle": "Minimal Valid Study",
                }
            }
        }
    ]

    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=studies,
    )

    ticker_resolver.prepare_company_search_name.return_value = (
        "Example"
    )

    events = provider.fetch_events("TEST")

    assert len(events) == 1
    assert events[0].summary == "NCT ID: NCT00000003"
    assert events[0].published_at is None


def test_fetch_events_converts_multiple_studies() -> None:
    identity = CompanyIdentity(
        ticker="TEST",
        company_name="Example Inc.",
    )

    studies = [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000010",
                    "briefTitle": "First Study",
                }
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000020",
                    "briefTitle": "Second Study",
                }
            }
        },
    ]

    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=studies,
    )

    ticker_resolver.prepare_company_search_name.return_value = (
        "Example"
    )

    events = provider.fetch_events("TEST")

    assert len(events) == 2
    assert events[0].title == "Clinical Trial — First Study"
    assert events[1].title == "Clinical Trial — Second Study"


def test_fetch_events_returns_empty_list_on_request_error() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    provider, ticker_resolver, client = build_provider(
        identity=identity
    )

    ticker_resolver.prepare_company_search_name.return_value = (
        "Liquidia"
    )
    client.search_studies.side_effect = (
        requests.RequestException("Network failure")
    )

    events = provider.fetch_events("LQDA")

    assert events == []


def test_fetch_events_passes_custom_max_events() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    provider, ticker_resolver, client = build_provider(
        identity=identity,
        max_events=3,
    )

    ticker_resolver.prepare_company_search_name.return_value = (
        "Liquidia"
    )

    provider.fetch_events("LQDA")

    client.search_studies.assert_called_once_with(
        query="Liquidia",
        page_size=3,
    )


def test_provider_rejects_invalid_max_events() -> None:
    try:
        ClinicalTrialsProvider(max_events=0)
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
    test_fetch_events_uses_prepared_company_name()
    test_fetch_events_returns_empty_list_for_empty_search_name()
    test_fetch_events_converts_study_to_event()
    test_fetch_events_uses_start_date_when_post_date_missing()
    test_fetch_events_skips_studies_without_required_fields()
    test_fetch_events_builds_summary_without_optional_fields()
    test_fetch_events_converts_multiple_studies()
    test_fetch_events_returns_empty_list_on_request_error()
    test_fetch_events_passes_custom_max_events()
    test_provider_rejects_invalid_max_events()

    print("ClinicalTrialsProvider tests passed.")