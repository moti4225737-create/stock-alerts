from datetime import date
from unittest.mock import Mock

from models.company_identity import CompanyIdentity
from modules.clinical_trials_provider import ClinicalTrialsProvider


def build_provider(
    studies: list[dict],
    max_age_days: int = 90,
) -> ClinicalTrialsProvider:
    ticker_resolver = Mock()
    ticker_resolver.get_company_identity.return_value = (
        CompanyIdentity(
            ticker="LQDA",
            company_name="Liquidia Corp",
        )
    )
    ticker_resolver.prepare_company_search_name.return_value = (
        "Liquidia"
    )

    client = Mock()
    client.search_studies.return_value = studies

    return ClinicalTrialsProvider(
        client=client,
        ticker_resolver=ticker_resolver,
        max_age_days=max_age_days,
        today_provider=lambda: date(2026, 7, 27),
    )


def build_study(
    nct_id: str,
    title: str,
    first_post_date: str,
    last_update_date: str | None = None,
) -> dict:
    status_module = {
        "studyFirstPostDateStruct": {
            "date": first_post_date,
        }
    }

    if last_update_date is not None:
        status_module["lastUpdatePostDateStruct"] = {
            "date": last_update_date,
        }

    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": nct_id,
                "briefTitle": title,
            },
            "statusModule": status_module,
        }
    }


def test_recent_last_update_keeps_old_study() -> None:
    studies = [
        build_study(
            nct_id="NCT00000001",
            title="Old Study With Recent Update",
            first_post_date="2015-06-17",
            last_update_date="2026-07-20",
        )
    ]

    provider = build_provider(studies)

    events = provider.fetch_events("LQDA")

    assert len(events) == 1
    assert events[0].published_at == "2026-07-20"


def test_old_last_update_is_filtered_out() -> None:
    studies = [
        build_study(
            nct_id="NCT00000002",
            title="Old Study Without Recent Activity",
            first_post_date="2015-06-17",
            last_update_date="2025-12-01",
        )
    ]

    provider = build_provider(studies)

    events = provider.fetch_events("LQDA")

    assert events == []


def test_first_post_date_is_used_when_update_date_missing() -> None:
    studies = [
        build_study(
            nct_id="NCT00000003",
            title="Recently Published Study",
            first_post_date="2026-07-10",
        )
    ]

    provider = build_provider(studies)

    events = provider.fetch_events("LQDA")

    assert len(events) == 1
    assert events[0].published_at == "2026-07-10"


def test_old_first_post_date_is_filtered_when_update_missing() -> None:
    studies = [
        build_study(
            nct_id="NCT00000004",
            title="Old Study Without Update Date",
            first_post_date="2020-12-10",
        )
    ]

    provider = build_provider(studies)

    events = provider.fetch_events("LQDA")

    assert events == []


def test_provider_rejects_invalid_max_age_days() -> None:
    try:
        ClinicalTrialsProvider(max_age_days=0)
    except ValueError as error:
        assert str(error) == "max_age_days must be at least 1"
    else:
        raise AssertionError(
            "Expected ValueError for max_age_days below 1."
        )