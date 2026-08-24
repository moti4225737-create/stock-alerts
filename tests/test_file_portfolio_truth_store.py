import json
from datetime import datetime, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest

from models.portfolio_holding import PortfolioHolding


def _contracts():
    truth_module = import_module("models.accepted_portfolio_truth")
    store_module = import_module("modules.file_portfolio_truth_store")
    return (
        truth_module.AcceptedPortfolioTruth,
        store_module.FilePortfolioTruthStore,
        store_module.PortfolioTruthStorageError,
        store_module,
    )


def _truth(symbol: str = "AAPL", quantity: str = "7.99"):
    AcceptedPortfolioTruth, _, _, _ = _contracts()
    return AcceptedPortfolioTruth(
        positions=(
            PortfolioHolding(
                symbol=symbol,
                quantity=Decimal(quantity),
            ),
        ),
        source_as_of=datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc),
        accepted_at=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
    )


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_save_and_load_round_trip_exact_accepted_truth(tmp_path) -> None:
    _, FilePortfolioTruthStore, _, _ = _contracts()
    path = tmp_path / "portfolio_state.json"
    original = _truth()

    FilePortfolioTruthStore(path).save(original)
    restored = FilePortfolioTruthStore(path).load()

    assert restored == original
    assert restored.positions[0].quantity == Decimal("7.99")
    assert isinstance(restored.positions[0].quantity, Decimal)


def test_decimal_quantity_is_serialized_as_exact_string(tmp_path) -> None:
    _, FilePortfolioTruthStore, _, _ = _contracts()
    path = tmp_path / "portfolio_state.json"

    FilePortfolioTruthStore(path).save(_truth(quantity="7.99"))
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["positions"][0]["quantity"] == "7.99"


def test_empty_accepted_truth_round_trips_as_present_truth(tmp_path) -> None:
    AcceptedPortfolioTruth, FilePortfolioTruthStore, _, _ = _contracts()
    path = tmp_path / "portfolio_state.json"
    original = AcceptedPortfolioTruth(
        positions=(),
        source_as_of=datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc),
        accepted_at=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
    )

    FilePortfolioTruthStore(path).save(original)
    restored = FilePortfolioTruthStore(path).load()

    assert restored is not None
    assert restored == original
    assert restored.positions == ()


def test_missing_state_file_returns_absence(tmp_path) -> None:
    _, FilePortfolioTruthStore, _, _ = _contracts()

    assert FilePortfolioTruthStore(tmp_path / "missing.json").load() is None


def test_malformed_state_fails_visibly(tmp_path) -> None:
    _, FilePortfolioTruthStore, PortfolioTruthStorageError, _ = _contracts()
    path = tmp_path / "portfolio_state.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(PortfolioTruthStorageError):
        FilePortfolioTruthStore(path).load()


@pytest.mark.parametrize(
    "payload",
    [
        {
            "source_as_of": "2026-08-24T12:00:00+00:00",
            "accepted_at": "2026-08-24T13:00:00+00:00",
        },
        {
            "positions": {},
            "source_as_of": "2026-08-24T12:00:00+00:00",
            "accepted_at": "2026-08-24T13:00:00+00:00",
        },
        {
            "positions": [],
            "accepted_at": "2026-08-24T13:00:00+00:00",
        },
        {
            "positions": [],
            "source_as_of": "2026-08-24T12:00:00+00:00",
        },
    ],
)
def test_structurally_invalid_state_fails_visibly(tmp_path, payload) -> None:
    _, FilePortfolioTruthStore, PortfolioTruthStorageError, _ = _contracts()
    path = tmp_path / "portfolio_state.json"
    _write_json(path, payload)

    with pytest.raises(PortfolioTruthStorageError):
        FilePortfolioTruthStore(path).load()


def test_invalid_persisted_holding_fails_visibly(tmp_path) -> None:
    _, FilePortfolioTruthStore, PortfolioTruthStorageError, _ = _contracts()
    path = tmp_path / "portfolio_state.json"
    _write_json(
        path,
        {
            "positions": [{"symbol": "AAPL", "quantity": "0"}],
            "source_as_of": "2026-08-24T12:00:00+00:00",
            "accepted_at": "2026-08-24T13:00:00+00:00",
        },
    )

    with pytest.raises(PortfolioTruthStorageError):
        FilePortfolioTruthStore(path).load()


def test_successful_save_leaves_complete_valid_json(tmp_path) -> None:
    _, FilePortfolioTruthStore, _, _ = _contracts()
    path = tmp_path / "portfolio_state.json"

    FilePortfolioTruthStore(path).save(_truth())
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert set(payload) == {"positions", "source_as_of", "accepted_at"}
    assert isinstance(payload["positions"], list)


def test_save_uses_same_directory_atomic_replacement(
    tmp_path,
    monkeypatch,
) -> None:
    _, FilePortfolioTruthStore, _, store_module = _contracts()
    path = tmp_path / "portfolio_state.json"
    real_replace = store_module.os.replace
    replacements = []

    def recording_replace(source, destination):
        replacements.append((source, destination))
        return real_replace(source, destination)

    monkeypatch.setattr(store_module.os, "replace", recording_replace)

    FilePortfolioTruthStore(path).save(_truth())

    assert len(replacements) == 1
    temporary_path, destination_path = map(Path, replacements[0])
    assert temporary_path.parent == path.parent
    assert destination_path == path


def test_fsync_failure_preserves_destination_and_cleans_temporary_file(
    tmp_path,
    monkeypatch,
) -> None:
    _, FilePortfolioTruthStore, PortfolioTruthStorageError, store_module = (
        _contracts()
    )
    path = tmp_path / "portfolio_state.json"
    store = FilePortfolioTruthStore(path)
    original = _truth()
    store.save(original)

    def failing_fsync(_file_descriptor):
        raise OSError("fsync failed")

    monkeypatch.setattr(store_module.os, "fsync", failing_fsync)

    with pytest.raises(PortfolioTruthStorageError):
        store.save(_truth(symbol="MSFT", quantity="2"))

    assert FilePortfolioTruthStore(path).load() == original
    assert set(tmp_path.iterdir()) == {path}


def test_replace_failure_preserves_destination_and_cleans_temporary_file(
    tmp_path,
    monkeypatch,
) -> None:
    _, FilePortfolioTruthStore, PortfolioTruthStorageError, store_module = (
        _contracts()
    )
    path = tmp_path / "portfolio_state.json"
    store = FilePortfolioTruthStore(path)
    original = _truth()
    store.save(original)

    def failing_replace(_source, _destination):
        raise OSError("replace failed")

    monkeypatch.setattr(store_module.os, "replace", failing_replace)

    with pytest.raises(PortfolioTruthStorageError):
        store.save(_truth(symbol="MSFT", quantity="2"))

    assert FilePortfolioTruthStore(path).load() == original
    assert set(tmp_path.iterdir()) == {path}
