import json
from dataclasses import asdict, replace

import pytest

from models.source_observation import SourceObservationState
from modules.file_source_observation_store import (
    FileSourceObservationStore,
    SourceObservationStorageError,
)


def _state():
    return SourceObservationState(
        schema="stock-sentinel.source-observation",
        version=1,
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
        objects={"NCT01234567": {"overall_status": "RECRUITING"}},
        pending=(),
        observed_through="2026-09-05",
    )


def test_persisted_observation_round_trips_from_fresh_store(tmp_path):
    state = replace(_state(), pending=({"event_id": "test-event"},))
    FileSourceObservationStore(tmp_path).save(state)

    assert FileSourceObservationStore(tmp_path).load(
        source=state.source, scope=state.scope,
    ) == state


@pytest.mark.parametrize("field,value", [
    ("schema", "unrelated-schema"),
    ("version", 999),
    ("objects", []),
    ("scope", "another-scope"),
])
def test_invalid_persisted_observation_is_rejected(tmp_path, field, value):
    state = _state()
    payload = asdict(state)
    payload[field] = value
    store = FileSourceObservationStore(tmp_path)
    store._state_path(state.source, state.scope).write_text(
        json.dumps(payload), encoding="utf-8",
    )

    with pytest.raises(SourceObservationStorageError):
        store.load(source=state.source, scope=state.scope)


@pytest.mark.parametrize("existing", [False, True], ids=["first-save", "advance"])
def test_failed_replacement_does_not_publish_advanced_state(tmp_path, monkeypatch, existing):
    store = FileSourceObservationStore(tmp_path)
    original = _state()
    if existing:
        store.save(original)
    advanced = replace(
        original,
        objects={"NCT01234567": {"overall_status": "COMPLETED"}},
        pending=({"event_id": "new-event"},),
        observed_through="2026-09-06",
    )
    calls = []

    def fail_replace(source, destination):
        calls.append(destination)
        assert source.exists()
        assert FileSourceObservationStore(tmp_path).load(
            source=original.source, scope=original.scope,
        ) == (original if existing else None)
        raise OSError("replacement failed")

    monkeypatch.setattr("modules.file_source_observation_store.os.replace", fail_replace)
    with pytest.raises(SourceObservationStorageError, match="Unable to save"):
        store.save(advanced)

    assert len(calls) == 1
    assert FileSourceObservationStore(tmp_path).load(
        source=original.source, scope=original.scope,
    ) == (original if existing else None)
    assert list(tmp_path.glob("*.tmp")) == []


def test_legacy_record_loads_without_inventing_observation_boundary(tmp_path) -> None:
    store = FileSourceObservationStore(tmp_path)
    state_path = store._state_path("ClinicalTrials.gov", "LQDA:liquidia")
    state_path.write_text(
        json.dumps({
            "schema": "stock-sentinel.source-observation",
            "version": 1,
            "source": "ClinicalTrials.gov",
            "scope": "LQDA:liquidia",
            "objects": {"NCT01234567": {"overall_status": "RECRUITING"}},
            "pending": [],
        }),
        encoding="utf-8",
    )

    restored = store.load(
        source="ClinicalTrials.gov",
        scope="LQDA:liquidia",
    )

    assert restored is not None
    assert restored.observed_through is None
