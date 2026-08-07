from datetime import datetime, time, timezone

from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_publication_window_respects_source_timezone() -> None:
    policy = SourceAcquisitionPolicy(
        source_name="ClinicalTrials.gov",
        interval_seconds=3600,
        publication_time=time(hour=9),
        publication_window_minutes=15,
        publication_interval_seconds=60,
        publication_timezone="America/New_York",
    )

    inside_window_utc = datetime(
        2026,
        8,
        7,
        12,
        50,
        tzinfo=timezone.utc,
    )

    outside_window_utc = datetime(
        2026,
        8,
        7,
        13,
        20,
        tzinfo=timezone.utc,
    )

    assert policy.interval_at_datetime(inside_window_utc) == 60
    assert policy.interval_at_datetime(outside_window_utc) == 3600
