import json
from datetime import timedelta
from decimal import Decimal
from importlib import import_module

import pytest


def _contracts():
    source_contract = import_module("application.portfolio_source")
    source_module = import_module("modules.json_file_portfolio_source")
    return source_contract.PortfolioSource, source_module.JsonFilePortfolioSource


def _write_candidate(tmp_path, payload):
    path = tmp_path / "portfolio_source.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _payload(**overrides):
    payload = {
        "source_as_of": "2026-08-24T12:00:00+00:00",
        "completeness": "complete",
        "positions": [
            {
                "symbol": "  aapl  ",
                "quantity": "7.99",
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_json_file_source_satisfies_portfolio_source_protocol(tmp_path) -> None:
    PortfolioSource, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(tmp_path / "portfolio_source.json")

    assert callable(getattr(PortfolioSource, "acquire"))
    assert callable(source.acquire)


def test_complete_json_produces_successful_candidate(tmp_path) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(_write_candidate(tmp_path, _payload()))

    result = source.acquire()

    assert result.candidate is not None
    assert result.candidate.completeness.value == "complete"
    assert result.candidate.source_as_of.tzinfo is not None


def test_non_utc_source_as_of_is_accepted_with_its_offset(tmp_path) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(
        _write_candidate(
            tmp_path,
            _payload(source_as_of="2026-08-24T15:00:00+03:00"),
        )
    )

    result = source.acquire()

    assert result.candidate is not None
    assert result.candidate.source_as_of.tzinfo is not None
    assert result.candidate.source_as_of.utcoffset() == timedelta(hours=3)


def test_quantity_and_symbol_use_portfolio_holding_semantics(tmp_path) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(_write_candidate(tmp_path, _payload()))

    holding = source.acquire().candidate.positions[0]

    assert holding.quantity == Decimal("7.99")
    assert isinstance(holding.quantity, Decimal)
    assert holding.symbol == "AAPL"
    assert holding.average_cost is None


def test_complete_empty_json_is_success_not_acquisition_failure(tmp_path) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(
        _write_candidate(tmp_path, _payload(positions=[]))
    )

    result = source.acquire()

    assert result.candidate is not None
    assert result.candidate.positions == ()
    assert result.candidate.is_eligible_for_acceptance is True


def test_missing_candidate_file_is_acquisition_failure(tmp_path) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(tmp_path / "missing.json")

    assert source.acquire().candidate is None


def test_unreadable_candidate_path_is_acquisition_failure(tmp_path) -> None:
    _, JsonFilePortfolioSource = _contracts()

    assert JsonFilePortfolioSource(tmp_path).acquire().candidate is None


def test_malformed_json_is_acquisition_failure(tmp_path) -> None:
    _, JsonFilePortfolioSource = _contracts()
    path = tmp_path / "portfolio_source.json"
    path.write_text("{not-json", encoding="utf-8")

    assert JsonFilePortfolioSource(path).acquire().candidate is None


@pytest.mark.parametrize(
    "payload",
    [
        {
            "source_as_of": "2026-08-24T12:00:00+00:00",
            "completeness": "complete",
        },
        {
            "source_as_of": "2026-08-24T12:00:00+00:00",
            "completeness": "complete",
            "positions": {},
        },
        {"completeness": "complete", "positions": []},
        {
            "source_as_of": "2026-08-24T12:00:00+00:00",
            "positions": [],
        },
        {
            "source_as_of": "2026-08-24T12:00:00+00:00",
            "completeness": "invalid",
            "positions": [],
        },
    ],
)
def test_structurally_invalid_json_is_acquisition_failure(
    tmp_path,
    payload,
) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(_write_candidate(tmp_path, payload))

    assert source.acquire().candidate is None


@pytest.mark.parametrize(
    "position",
    [
        {"symbol": "   ", "quantity": "1"},
        {"symbol": "AAPL", "quantity": "not-a-number"},
        {"symbol": "AAPL", "quantity": "0"},
        {"symbol": "AAPL", "quantity": "-1"},
    ],
)
def test_invalid_holding_is_acquisition_failure(tmp_path, position) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(
        _write_candidate(tmp_path, _payload(positions=[position]))
    )

    assert source.acquire().candidate is None


@pytest.mark.parametrize("completeness", ["partial", "unknown"])
def test_non_complete_observation_remains_successful_candidate(
    tmp_path,
    completeness,
) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(
        _write_candidate(tmp_path, _payload(completeness=completeness))
    )

    result = source.acquire()

    assert result.candidate is not None
    assert result.candidate.completeness.value == completeness
    assert result.candidate.is_eligible_for_acceptance is False


def test_naive_source_as_of_is_acquisition_failure(tmp_path) -> None:
    _, JsonFilePortfolioSource = _contracts()
    source = JsonFilePortfolioSource(
        _write_candidate(
            tmp_path,
            _payload(source_as_of="2026-08-24T12:00:00"),
        )
    )

    assert source.acquire().candidate is None
