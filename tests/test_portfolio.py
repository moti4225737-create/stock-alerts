from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding


def test_portfolio_holding_defaults_to_optional_average_cost():
    holding = PortfolioHolding(symbol="AAPL", quantity=10)

    assert holding.symbol == "AAPL"
    assert holding.quantity == 10
    assert holding.average_cost is None


def test_portfolio_can_store_holdings_and_lookup_by_symbol():
    holding = PortfolioHolding(symbol="AAPL", quantity=10, average_cost=150.0)
    portfolio = Portfolio([holding])

    assert portfolio.holdings == [holding]
    assert portfolio.get("AAPL") == holding
    assert portfolio.get("MSFT") is None


def test_portfolio_rejects_duplicate_symbols():
    first = PortfolioHolding(symbol="AAPL", quantity=10)
    second = PortfolioHolding(symbol="AAPL", quantity=5)

    try:
        Portfolio([first, second])
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("Portfolio should reject duplicate symbols")


def test_empty_portfolio_is_supported():
    portfolio = Portfolio([])

    assert portfolio.holdings == []
    assert portfolio.get("AAPL") is None
