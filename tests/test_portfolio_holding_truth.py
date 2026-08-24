from dataclasses import fields
from decimal import Decimal

import pytest

from models.portfolio_holding import PortfolioHolding


def test_fractional_quantity_is_preserved_as_decimal() -> None:
    holding = PortfolioHolding(
        symbol="LQDA",
        quantity=Decimal("7.99"),
    )

    assert holding.quantity == Decimal("7.99")
    assert isinstance(holding.quantity, Decimal)


def test_whole_share_quantity_is_normalized_to_decimal() -> None:
    holding = PortfolioHolding(symbol="AAPL", quantity=10)

    assert holding.quantity == Decimal("10")
    assert isinstance(holding.quantity, Decimal)


def test_symbol_is_stripped_and_uppercased() -> None:
    holding = PortfolioHolding(symbol="  aapl  ", quantity=Decimal("1"))

    assert holding.symbol == "AAPL"


@pytest.mark.parametrize("symbol", ["", " ", "\t\r\n"])
def test_blank_symbol_is_rejected(symbol: str) -> None:
    with pytest.raises(ValueError, match="symbol"):
        PortfolioHolding(symbol=symbol, quantity=Decimal("1"))


def test_average_cost_may_be_absent() -> None:
    holding = PortfolioHolding(symbol="AAPL", quantity=Decimal("1"))

    assert holding.average_cost is None


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("0"),
        Decimal("-0.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_non_positive_or_non_finite_quantity_is_rejected(
    quantity: Decimal,
) -> None:
    with pytest.raises(ValueError, match="quantity"):
        PortfolioHolding(symbol="AAPL", quantity=quantity)


def test_synchronization_metadata_is_not_part_of_holding() -> None:
    holding_field_names = {field.name for field in fields(PortfolioHolding)}

    assert holding_field_names.isdisjoint(
        {
            "source_as_of",
            "completeness",
            "sync_status",
            "latest_attempt_at",
        }
    )
