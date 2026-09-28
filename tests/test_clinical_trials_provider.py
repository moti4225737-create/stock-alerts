from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest
import requests

from models.company_identity import CompanyIdentity
from models.event import Event
from models.source_observation import SourceObservationState
from modules.clinical_trials_provider import (
    ClinicalTrialsProvider,
)
from modules.data_provider import DataProvider
from datetime import datetime, timezone
from modules.file_source_observation_store import FileSourceObservationStore


def _g1_ct(tmp_path, studies, boundary="2026-07-20T12:00:00+00:00"):
    resolver = Mock()
    resolver.get_company_identity.return_value = CompanyIdentity(ticker="LQDA", company_name="Liquidia")
    resolver.prepare_company_search_name.return_value = "Liquidia"
    client = Mock()
    client.search_studies.return_value = ClinicalTrialsPage(studies, None)
    store = FileSourceObservationStore(tmp_path)
    provider = ClinicalTrialsProvider(client=client, ticker_resolver=resolver,
        source_observation_store=store, today_provider=lambda: date(2026, 7, 27),
        time_zero_for=lambda symbol: datetime.fromisoformat(boundary))
    return provider, store


def _g1_ct_study(status="RECRUITING", first="2026-07-01", update="2026-07-21"):
    study = paginated_study("NCT01234567", status)
    study["protocolSection"]["statusModule"].update({
        "studyFirstPostDateStruct": {"date": first},
        "lastUpdatePostDateStruct": {"date": update},
    })
    return study


def _g1_ct_seed(provider, store, studies):
    store.save(SourceObservationState(schema="stock-sentinel.source-observation",
        version=1, source="ClinicalTrials.gov", scope="LQDA:liquidia",
        objects=provider._canonical_observation(studies), observed_through="2026-07-20"))


def test_g1_ct_historical_study_is_observed_not_new(tmp_path):
    study = _g1_ct_study(update="2026-07-19")
    provider, store = _g1_ct(tmp_path, [study])
    _g1_ct_seed(provider, store, [])
    assert provider.fetch_events("LQDA") == [], "Historical discovery cannot become new study"
    state = store.load(source="ClinicalTrials.gov", scope="LQDA:liquidia")
    assert "NCT01234567" in state.objects
    assert state.pending == ()


def test_g1_ct_live_change_on_old_study_is_eligible(tmp_path):
    provider, store = _g1_ct(tmp_path, [_g1_ct_study("COMPLETED")])
    _g1_ct_seed(provider, store, [_g1_ct_study()])
    events = provider.fetch_events("LQDA")
    assert len(events) == 1
    assert store.load(source="ClinicalTrials.gov", scope="LQDA:liquidia").pending[0]["event_id"] == events[0].event_id


def test_g1_ct_first_complete_acquisition_does_not_swallow_live_study(tmp_path):
    provider, store = _g1_ct(tmp_path, [_g1_ct_study(first="2026-07-21")])
    events = provider.fetch_events("LQDA")
    assert len(events) == 1, "Source bootstrap is not another admission gate after READY"
    assert store.load(source="ClinicalTrials.gov", scope="LQDA:liquidia").pending


def test_g1_ct_pending_replay_respects_current_lifecycle_boundary(tmp_path):
    provider, store = _g1_ct(tmp_path, [_g1_ct_study("COMPLETED")])
    _g1_ct_seed(provider, store, [_g1_ct_study()])
    assert len(provider.fetch_events("LQDA")) == 1
    restarted, _ = _g1_ct(tmp_path, [], boundary="2026-07-25T12:00:00+00:00")
    assert restarted.fetch_events("LQDA") == [], "Old-lifecycle pending cannot bypass time_zero"


def test_g2_ct_repeated_transition_distinguishes_occurrence_after_restart(tmp_path):
    provider, store = _g1_ct(tmp_path, [])
    _g1_ct_seed(provider, store, [_g1_ct_study("RECRUITING")])
    ids = []
    transitions = (
        ("COMPLETED", "2026-07-21"),
        ("RECRUITING", "2026-07-22"),
        ("COMPLETED", "2026-07-23"),
    )
    for status, update in transitions:
        provider, store = _g1_ct(
            tmp_path,
            [_g1_ct_study(status, update=update)],
        )
        events = provider.fetch_events("LQDA")
        assert len(events) == 1
        ids.append(events[0].event_id)
        replay, _ = _g1_ct(tmp_path, [])
        assert replay.fetch_events("LQDA")[0].event_id == ids[-1]
        replay.acknowledge_pending()
        unchanged, _ = _g1_ct(
            tmp_path,
            [_g1_ct_study(status, update=update)],
        )
        assert unchanged.fetch_events("LQDA") == []
    assert ids[0] != ids[2], "Second A-to-B is a distinct persisted occurrence"


TEST_TODAY = date(2026, 7, 27)
RECENT_DATE = "2026-07-20"


class ClinicalTrialsPage(list):
    def __init__(self, studies: list[dict], next_page_token: str | None):
        super().__init__(studies)
        self.next_page_token = next_page_token


def paginated_study(nct_id: str, status: str) -> dict:
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": nct_id,
                "briefTitle": f"Study {nct_id}",
            },
            "statusModule": {
                "overallStatus": status,
                "studyFirstPostDateStruct": {"date": RECENT_DATE},
            },
        }
    }


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
        today_provider=lambda: TEST_TODAY,
    )

    return provider, ticker_resolver, client


def build_recent_status_module(
    overall_status: str | None = None,
) -> dict:
    status_module: dict = {
        "studyFirstPostDateStruct": {
            "date": RECENT_DATE,
        }
    }

    if overall_status is not None:
        status_module["overallStatus"] = overall_status

    return status_module


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
                        "date": RECENT_DATE,
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
    assert event.published_at == RECENT_DATE
    assert event.importance == 2
    assert event.sentiment == "neutral"
    assert event.url == (
        "https://clinicaltrials.gov/study/NCT01234567"
    )

    client.search_studies.assert_called_once_with(
        query="Liquidia",
        page_size=10,
    )


def test_first_complete_observation_persists_nct_identity() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )
    studies = [{
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT01234567",
                "briefTitle": "Historical Yutrepia Study",
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "studyFirstPostDateStruct": {
                    "date": RECENT_DATE,
                },
            },
        }
    }]
    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=studies,
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = None
    provider._source_observation_store = observation_store

    provider.fetch_events("LQDA")

    observation_store.save.assert_called_once()
    persisted_state = observation_store.save.call_args.args[0]
    assert set(persisted_state.objects) == {"NCT01234567"}


def test_first_complete_observation_persists_observed_through() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=[paginated_study("NCT01234567", "RECRUITING")],
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = None
    provider._source_observation_store = observation_store

    assert provider.fetch_events("LQDA") == []

    saved = observation_store.save.call_args.args[0]
    assert saved.observed_through == "2026-07-27"
    assert saved.pending == ()


def test_first_complete_observation_returns_zero_historical_events() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )
    studies = [{
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT01234567",
                "briefTitle": "Historical Yutrepia Study",
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "studyFirstPostDateStruct": {
                    "date": RECENT_DATE,
                },
            },
        }
    }]
    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=studies,
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = None
    provider._source_observation_store = observation_store

    events = provider.fetch_events("LQDA")

    assert events == []


def test_terminal_pages_form_one_complete_zero_event_first_observation() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    provider, ticker_resolver, client = build_provider(identity=identity)
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    client.search_studies.side_effect = [
        ClinicalTrialsPage(
            [paginated_study("NCT00000001", "RECRUITING")],
            "TOKEN_2",
        ),
        ClinicalTrialsPage(
            [paginated_study("NCT00000002", "COMPLETED")],
            None,
        ),
    ]
    observation_store = Mock()
    observation_store.load.return_value = None
    provider._source_observation_store = observation_store

    events = provider.fetch_events("LQDA")

    assert client.search_studies.call_args_list == [
        call(query="Liquidia", page_size=10),
        call(query="Liquidia", page_size=10, page_token="TOKEN_2"),
    ]
    assert events == []
    observation_store.save.assert_called_once()
    saved = observation_store.save.call_args.args[0]
    assert set(saved.objects) == {"NCT00000001", "NCT00000002"}


def test_pagination_continues_past_legacy_page_cap_until_source_termination() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    provider, ticker_resolver, client = build_provider(identity=identity)
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    client.search_studies.side_effect = [
        ClinicalTrialsPage(
            [paginated_study("NCT01234567", "COMPLETED")],
            "TOKEN_2",
        ),
        ClinicalTrialsPage(
            [paginated_study("NCT07654321", "RECRUITING")],
            None,
        ),
    ]
    observation_store = Mock()
    observation_store.load.return_value = None
    provider._source_observation_store = observation_store

    events = provider.fetch_events("LQDA")

    assert client.search_studies.call_args_list == [
        call(query="Liquidia", page_size=10),
        call(query="Liquidia", page_size=10, page_token="TOKEN_2"),
    ]
    assert events == []
    observation_store.save.assert_called_once()
    saved = observation_store.save.call_args.args[0]
    assert set(saved.objects) == {"NCT01234567", "NCT07654321"}


def test_later_page_failure_preserves_authoritative_observation() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    provider, ticker_resolver, client = build_provider(identity=identity)
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    client.search_studies.side_effect = [
        ClinicalTrialsPage(
            [paginated_study("NCT01234567", "COMPLETED")],
            "TOKEN_2",
        ),
        requests.RequestException("later page failed"),
    ]
    authoritative = SourceObservationState(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects=provider._canonical_observation([
            paginated_study("NCT01234567", "RECRUITING")
        ]),
        pending=(),
    )
    observation_store = Mock()
    observation_store.load.return_value = authoritative
    provider._source_observation_store = observation_store

    with pytest.raises(requests.RequestException):
        provider.fetch_events("LQDA")

    assert client.search_studies.call_count == 2
    observation_store.save.assert_not_called()
    assert observation_store.load.return_value is authoritative


def _incremental_state(provider: ClinicalTrialsProvider, studies: list[dict]):
    return SimpleNamespace(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects=provider._canonical_observation(studies),
        pending=(),
        observed_through="2026-07-20",
    )


def test_steady_state_uses_overlapping_last_update_query_term() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    study = paginated_study("NCT01234567", "RECRUITING")
    provider, ticker_resolver, client = build_provider(
        identity=identity,
        studies=[study],
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = _incremental_state(provider, [study])
    provider._source_observation_store = observation_store

    provider.fetch_events("LQDA")

    client.search_studies.assert_called_once_with(
        query_term=(
            'AREA[SponsorSearch]"Liquidia" AND '
            'AREA[LastUpdatePostDate]RANGE[2026-07-19, MAX]'
        ),
        page_size=10,
    )


def test_zero_change_steady_state_merges_and_advances_boundary() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    historical = paginated_study("NCT00000001", "COMPLETED")
    returned = paginated_study("NCT01234567", "RECRUITING")
    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=[returned],
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = _incremental_state(
        provider,
        [historical, returned],
    )
    provider._source_observation_store = observation_store

    assert provider.fetch_events("LQDA") == []

    observation_store.save.assert_called_once()
    saved = observation_store.save.call_args.args[0]
    assert set(saved.objects) == {"NCT00000001", "NCT01234567"}
    assert saved.observed_through == "2026-07-27"
    assert saved.pending == ()


def test_steady_status_change_preserves_absent_history_in_atomic_state() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    historical = paginated_study("NCT00000001", "COMPLETED")
    previous = paginated_study("NCT01234567", "RECRUITING")
    current = paginated_study("NCT01234567", "COMPLETED")
    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=[current],
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = _incremental_state(
        provider,
        [historical, previous],
    )
    provider._source_observation_store = observation_store

    events = provider.fetch_events("LQDA")

    assert len(events) == 1
    assert events[0].event_id == (
        "ClinicalTrials.gov|NCT01234567|overall_status|"
        "RECRUITING|COMPLETED"
    )
    saved = observation_store.save.call_args.args[0]
    assert set(saved.objects) == {"NCT00000001", "NCT01234567"}
    assert saved.observed_through == "2026-07-27"
    assert saved.pending[0]["event_id"] == events[0].event_id


def test_new_post_baseline_nct_is_one_deterministic_candidate() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    historical = paginated_study("NCT00000001", "COMPLETED")
    new_study = paginated_study("NCT01234567", "RECRUITING")
    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=[new_study],
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = _incremental_state(
        provider,
        [historical],
    )
    provider._source_observation_store = observation_store

    events = provider.fetch_events("LQDA")

    assert len(events) == 1
    assert events[0].event_id
    saved = observation_store.save.call_args.args[0]
    assert set(saved.objects) == {"NCT00000001", "NCT01234567"}
    assert saved.pending[0]["event_id"] == events[0].event_id


def test_legacy_state_without_boundary_rebaselines_without_events() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    historical = paginated_study("NCT00000001", "RECRUITING")
    current = paginated_study("NCT01234567", "COMPLETED")
    provider, ticker_resolver, client = build_provider(
        identity=identity,
        studies=[current],
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    legacy = SourceObservationState(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects=provider._canonical_observation([historical]),
        pending=(),
    )
    observation_store = Mock()
    observation_store.load.return_value = legacy
    provider._source_observation_store = observation_store

    events = provider.fetch_events("LQDA")

    assert events == []
    client.search_studies.assert_called_once_with(
        query="Liquidia",
        page_size=10,
    )
    saved = observation_store.save.call_args.args[0]
    assert set(saved.objects) == {"NCT01234567"}
    assert saved.observed_through == "2026-07-27"
    assert saved.pending == ()


def test_candidate_is_not_exposed_when_incremental_state_save_fails() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    previous = paginated_study("NCT01234567", "RECRUITING")
    current = paginated_study("NCT01234567", "COMPLETED")
    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=[current],
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = _incremental_state(provider, [previous])
    observation_store.save.side_effect = RuntimeError("atomic save failed")
    provider._source_observation_store = observation_store

    with pytest.raises(RuntimeError, match="atomic save failed"):
        provider.fetch_events("LQDA")


def test_existing_nct_status_transition_returns_one_deterministic_candidate() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )

    def study(status: str, title: str) -> dict:
        return {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT01234567",
                    "briefTitle": title,
                },
                "statusModule": {
                    "overallStatus": status,
                    "studyFirstPostDateStruct": {
                        "date": RECENT_DATE,
                    },
                },
            }
        }

    previous_study = study("RECRUITING", "Original Presentation Title")
    current_study = study("COMPLETED", "Changed Presentation Title")
    provider, ticker_resolver, _ = build_provider(
        identity=identity,
        studies=[current_study],
    )
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    observation_store = Mock()
    observation_store.load.return_value = SourceObservationState(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects=provider._canonical_observation([previous_study]),
        pending=(),
        observed_through="2026-07-20",
    )
    operation_order = []
    observation_store.save.side_effect = lambda state: operation_order.append(
        ("save", state)
    )
    provider._source_observation_store = observation_store

    events = provider.fetch_events("LQDA")
    operation_order.append(("return", events))

    assert len(events) == 1
    candidate = events[0]
    assert candidate.source == "ClinicalTrials.gov"
    assert candidate.url == "https://clinicaltrials.gov/study/NCT01234567"
    assert candidate.event_id == (
        "ClinicalTrials.gov|NCT01234567|overall_status|"
        "RECRUITING|COMPLETED"
    )
    assert "RECRUITING → COMPLETED" in candidate.summary
    observation_store.save.assert_called_once()
    saved_state = observation_store.save.call_args.args[0]
    assert saved_state.objects == provider._canonical_observation([current_study])
    assert saved_state.pending == ({
        "event_id": candidate.event_id,
        "symbol": candidate.symbol,
        "source": candidate.source,
        "title": candidate.title,
        "summary": candidate.summary,
        "published_at": candidate.published_at,
        "importance": candidate.importance,
        "sentiment": candidate.sentiment,
        "url": candidate.url,
    },)
    assert saved_state.pending[0]["event_id"] == (
        "ClinicalTrials.gov|NCT01234567|overall_status|"
        "RECRUITING|COMPLETED"
    )
    assert [step for step, _ in operation_order] == ["save", "return"]


def test_persisted_pending_candidate_replays_before_acquisition_after_restart() -> None:
    identity = CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )
    provider, ticker_resolver, client = build_provider(identity=identity)
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    current_study = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT01234567",
                "briefTitle": "Changed Presentation Title",
            },
            "statusModule": {
                "overallStatus": "COMPLETED",
                "studyFirstPostDateStruct": {
                    "date": RECENT_DATE,
                },
            },
        }
    }
    event_id = (
        "ClinicalTrials.gov|NCT01234567|overall_status|"
        "RECRUITING|COMPLETED"
    )
    pending = {
        "event_id": event_id,
        "symbol": "LQDA",
        "source": "ClinicalTrials.gov",
        "title": "Clinical Trial — Changed Presentation Title",
        "summary": (
            "NCT ID: NCT01234567 | Overall status changed: "
            "RECRUITING → COMPLETED"
        ),
        "published_at": RECENT_DATE,
        "importance": 2,
        "sentiment": "neutral",
        "url": "https://clinicaltrials.gov/study/NCT01234567",
    }
    persisted_state = SourceObservationState(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects=provider._canonical_observation([current_study]),
        pending=(pending,),
    )
    observation_store = Mock()
    observation_store.load.return_value = persisted_state
    provider._source_observation_store = observation_store

    events = provider.fetch_events("LQDA")

    client.search_studies.assert_not_called()
    assert len(events) == 1
    candidate = events[0]
    assert candidate.event_id == event_id
    assert {
        "event_id": candidate.event_id,
        "symbol": candidate.symbol,
        "source": candidate.source,
        "title": candidate.title,
        "summary": candidate.summary,
        "published_at": candidate.published_at,
        "importance": candidate.importance,
        "sentiment": candidate.sentiment,
        "url": candidate.url,
    } == pending
    assert observation_store.load.return_value is persisted_state
    assert persisted_state.objects["NCT01234567"]["overall_status"] == "COMPLETED"
    assert persisted_state.pending == (pending,)
    observation_store.save.assert_not_called()


def test_acknowledge_pending_clears_exposed_candidate_and_retains_objects() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    provider, ticker_resolver, client = build_provider(identity=identity)
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    pending = {
        "event_id": (
            "ClinicalTrials.gov|NCT01234567|overall_status|"
            "RECRUITING|COMPLETED"
        ),
        "symbol": "LQDA",
        "source": "ClinicalTrials.gov",
        "title": "Clinical Trial — Study",
        "summary": "RECRUITING → COMPLETED",
        "published_at": RECENT_DATE,
        "importance": 2,
        "sentiment": "neutral",
        "url": "https://clinicaltrials.gov/study/NCT01234567",
    }
    objects = {"NCT01234567": {"overall_status": "COMPLETED"}}
    state = SourceObservationState(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects=objects,
        pending=(pending,),
    )
    observation_store = Mock()
    observation_store.load.return_value = state
    provider._source_observation_store = observation_store

    assert [event.event_id for event in provider.fetch_events("LQDA")] == [
        pending["event_id"]
    ]
    provider.acknowledge_pending()

    client.search_studies.assert_not_called()
    observation_store.save.assert_called_once()
    cleared = observation_store.save.call_args.args[0]
    assert cleared.objects == objects
    assert cleared.pending == ()


def test_acknowledge_pending_retains_candidate_not_exposed_by_current_attempt() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    provider, ticker_resolver, client = build_provider(identity=identity)
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    exposed = {
        "event_id": "exposed-id",
        "symbol": "LQDA",
        "source": "ClinicalTrials.gov",
        "title": "Exposed",
        "summary": "Exposed",
        "published_at": RECENT_DATE,
        "importance": 2,
        "sentiment": "neutral",
        "url": "https://clinicaltrials.gov/study/NCT01234567",
    }
    unexposed = {**exposed, "event_id": "unexposed-id", "title": "Unexposed"}
    objects = {"NCT01234567": {"overall_status": "COMPLETED"}}
    replay_state = SourceObservationState(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects=objects,
        pending=(exposed,),
    )
    latest_state = SourceObservationState(
        schema=replay_state.schema,
        version=replay_state.version,
        source=replay_state.source,
        scope=replay_state.scope,
        objects=objects,
        pending=(exposed, unexposed),
    )
    observation_store = Mock()
    observation_store.load.side_effect = [replay_state, latest_state]
    provider._source_observation_store = observation_store

    provider.fetch_events("LQDA")
    provider.acknowledge_pending()

    client.search_studies.assert_not_called()
    saved = observation_store.save.call_args.args[0]
    assert saved.objects == objects
    assert saved.pending == (unexposed,)


def test_acknowledge_pending_propagates_clear_save_failure() -> None:
    identity = CompanyIdentity(ticker="LQDA", company_name="Liquidia Corp")
    provider, ticker_resolver, client = build_provider(identity=identity)
    ticker_resolver.prepare_company_search_name.return_value = "Liquidia"
    pending = {
        "event_id": "pending-id",
        "symbol": "LQDA",
        "source": "ClinicalTrials.gov",
        "title": "Pending",
        "summary": "Pending",
        "published_at": RECENT_DATE,
        "importance": 2,
        "sentiment": "neutral",
        "url": "https://clinicaltrials.gov/study/NCT01234567",
    }
    state = SourceObservationState(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects={"NCT01234567": {"overall_status": "COMPLETED"}},
        pending=(pending,),
    )
    observation_store = Mock()
    observation_store.load.return_value = state
    observation_store.save.side_effect = RuntimeError("clear failed")
    provider._source_observation_store = observation_store
    provider.fetch_events("LQDA")

    with pytest.raises(RuntimeError, match="clear failed"):
        provider.acknowledge_pending()

    client.search_studies.assert_not_called()
    assert state.pending == (pending,)


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
                },
                "statusModule": build_recent_status_module(),
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "briefTitle": "Study Without NCT ID",
                },
                "statusModule": build_recent_status_module(),
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000002",
                    "briefTitle": "Valid Example Study",
                },
                "statusModule": build_recent_status_module(
                    overall_status="COMPLETED"
                ),
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
    assert events[0].published_at == RECENT_DATE
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
                },
                "statusModule": build_recent_status_module(),
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
    assert events[0].published_at == RECENT_DATE


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
                },
                "statusModule": build_recent_status_module(),
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000020",
                    "briefTitle": "Second Study",
                },
                "statusModule": build_recent_status_module(),
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


def test_fetch_events_propagates_request_error() -> None:
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

    with pytest.raises(
        requests.RequestException,
        match="Network failure",
    ):
        provider.fetch_events("LQDA")


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
    test_fetch_events_skips_studies_without_required_fields()
    test_fetch_events_builds_summary_without_optional_fields()
    test_fetch_events_converts_multiple_studies()
    test_fetch_events_returns_empty_list_on_request_error()
    test_fetch_events_passes_custom_max_events()
    test_provider_rejects_invalid_max_events()

    print("ClinicalTrialsProvider tests passed.")

def test_g1_new_study_uses_first_post_not_later_update_for_time_zero(tmp_path):
    study = _g1_ct_study(
        "RECRUITING",
        first="2026-07-19",
        update="2026-07-21",
    )
    provider, store = _g1_ct(tmp_path, [study])

    events = provider.fetch_events("TEST")

    assert events == []


def test_g1_status_change_without_last_update_fails_closed_for_live_admission(tmp_path):
    provider, store = _g1_ct(
        tmp_path,
        [_g1_ct_study("RECRUITING", update="2026-07-19")],
    )
    assert provider.fetch_events("TEST") == []

    study = _g1_ct_study("COMPLETED", first="2026-07-21")
    del study["protocolSection"]["statusModule"]["lastUpdatePostDateStruct"]

    provider, store = _g1_ct(tmp_path, [study])

    events = provider.fetch_events("TEST")

    assert events == []
