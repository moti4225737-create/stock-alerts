from datetime import time

import pytest

from engines.source_acquisition_policy import SourceAcquisitionPolicy


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "publication_time": time(hour=9),
        },
        {
            "publication_window_minutes": 15,
        },
        {
            "publication_interval_seconds": 60,
        },
        {
            "publication_time": time(hour=9),
            "publication_window_minutes": 15,
        },
        {
            "publication_time": time(hour=9),
            "publication_interval_seconds": 60,
        },
        {
            "publication_window_minutes": 15,
            "publication_interval_seconds": 60,
        },
    ],
)
def test_source_acquisition_policy_rejects_partial_publication_configuration(
    kwargs,
) -> None:
    with pytest.raises(
        ValueError,
        match="publication configuration must be complete",
    ):
        SourceAcquisitionPolicy(
            source_name="ClinicalTrials.gov",
            interval_seconds=3600,
            **kwargs,
        )
