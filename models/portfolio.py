from collections.abc import Iterable

from models.portfolio_holding import PortfolioHolding


class Portfolio:
    def __init__(self, holdings: Iterable[PortfolioHolding] | None = None) -> None:
        self._holdings = list(holdings or [])
        self._validate_unique_symbols()

    @property
    def holdings(self) -> list[PortfolioHolding]:
        return self._holdings

    def get(self, symbol: str) -> PortfolioHolding | None:
        for holding in self._holdings:
            if holding.symbol == symbol:
                return holding
        return None

    def _validate_unique_symbols(self) -> None:
        symbols = [holding.symbol for holding in self._holdings]
        if len(symbols) != len(set(symbols)):
            raise ValueError("Portfolio contains duplicate symbols")
