from datetime import time

import pytest

from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_source_acquisition_policy_preserves_source_specific_cadence() -> None:
    policy = SourceAcquisitionPolicy(
        source_name="SEC",
        interval_seconds=60,
    )

    assert policy.source_name == "SEC"
    assert policy.interval_seconds == 60
    assert policy.publication_time is None


def test_source_acquisition_policy_preserves_complete_publication_configuration() -> None:
    policy = SourceAcquisitionPolicy(
        source_name="ClinicalTrials.gov",
        interval_seconds=3600,
        publication_time=time(hour=9),
        publication_window_minutes=15,
        publication_interval_seconds=60,
        publication_timezone="America/New_York",
    )

    assert policy.source_name == "ClinicalTrials.gov"
    assert policy.interval_seconds == 3600
    assert policy.publication_time == time(hour=9)
    assert policy.publication_window_minutes == 15
    assert policy.publication_interval_seconds == 60
    assert policy.publication_timezone == "America/New_York"


def test_source_acquisition_policy_rejects_empty_source_name() -> None:
    with pytest.raises(
        ValueError,
        match="source_name must not be empty",
    ):
        SourceAcquisitionPolicy(
            source_name="   ",
            interval_seconds=60,
        )


def test_source_acquisition_policy_rejects_non_positive_interval() -> None:
    with pytest.raises(
        ValueError,
        match="interval_seconds must be at least 1",
    ):
        SourceAcquisitionPolicy(
            source_name="SEC",
            interval_seconds=0,
        )


def test_publication_window_uses_faster_interval() -> None:
    policy = SourceAcquisitionPolicy(
        source_name="ClinicalTrials.gov",
        interval_seconds=3600,
        publication_time=time(hour=9),
        publication_window_minutes=15,
        publication_interval_seconds=60,
    )

    assert policy.interval_at(time(hour=8, minute=50)) == 60
    assert policy.interval_at(time(hour=9, minute=10)) == 60


def test_outside_publication_window_uses_normal_interval() -> None:
    policy = SourceAcquisitionPolicy(
        source_name="ClinicalTrials.gov",
        interval_seconds=3600,
        publication_time=time(hour=9),
        publication_window_minutes=15,
        publication_interval_seconds=60,
    )

    assert policy.interval_at(time(hour=8, minute=30)) == 3600
    assert policy.interval_at(time(hour=9, minute=30)) == 3600


def test_source_acquisition_policy_rejects_non_positive_publication_window() -> None:
    with pytest.raises(
        ValueError,
        match="publication_window_minutes must be at least 1",
    ):
        SourceAcquisitionPolicy(
            source_name="ClinicalTrials.gov",
            interval_seconds=3600,
            publication_time=time(hour=9),
            publication_window_minutes=0,
            publication_interval_seconds=60,
        )


def test_source_acquisition_policy_rejects_non_positive_publication_interval() -> None:
    with pytest.raises(
        ValueError,
        match="publication_interval_seconds must be at least 1",
    ):
        SourceAcquisitionPolicy(
            source_name="ClinicalTrials.gov",
            interval_seconds=3600,
            publication_time=time(hour=9),
            publication_window_minutes=15,
            publication_interval_seconds=0,
        )
