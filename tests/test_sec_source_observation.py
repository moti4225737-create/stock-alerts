from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from modules.sec_provider import SECProvider


@pytest.mark.parametrize("occurrence,live", [
    ("2026-07-19T12:00:00Z", False),
    ("2026-07-21T12:00:00Z", True),
    (None, False),
    ("invalid", False),
])
def test_g1_sec_observes_but_only_live_occurrences_enter_pending(monkeypatch, occurrence, live):
    monkeypatch.setenv("SEC_USER_AGENT", "unit-test test@example.test")
    store = Mock()
    store.load.return_value = None
    provider = SECProvider(
        source_observation_store=store,
        time_zero_for=lambda symbol: datetime(2026, 7, 20, 12, tzinfo=timezone.utc),
    )
    provider._get_cik = Mock(return_value="0000000001")
    provider._get_submissions = Mock(return_value={"filings": {"recent": {
        "form": ["8-K"], "filingDate": [occurrence[:10] if occurrence else ""],
        "acceptanceDateTime": [occurrence],
        "accessionNumber": ["0000000001-26-000001"],
        "primaryDocument": ["filing.htm"], "primaryDocDescription": ["Filing"],
    }}})
    events = provider.fetch_events("TEST")
    assert len(events) == int(live), "Only authoritative live filings may emit"
    assert store.save.called, "Acquired filings must reach Source Observation"
    state = store.save.call_args.args[0]
    assert state.objects, "Historical acquisition must remain learnable"
    assert len(state.pending) == int(live)
    if live:
        assert events[0].event_id
        assert state.pending[0]["event_id"] == events[0].event_id
