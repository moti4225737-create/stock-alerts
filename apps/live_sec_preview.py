import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from engines.portfolio_intelligence_service import PortfolioIntelligenceService
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from modules.sec_provider import SECProvider


def build_portfolio(symbols: list[str]) -> Portfolio:
    return Portfolio([PortfolioHolding(symbol=symbol, quantity=1) for symbol in symbols])


def build_live_briefs(symbols: list[str], provider: object) -> tuple[list[object], list[str]]:
    portfolio = build_portfolio(symbols)
    service = PortfolioIntelligenceService()
    return service.build_briefs(portfolio, provider)


def main() -> None:
    symbols = ["AAPL", "MSFT"]
    provider = SECProvider()
    briefs, errors = build_live_briefs(symbols, provider)

    if errors:
        for error in errors:
            print(f"error: {error}")

    for brief in briefs:
        print(
            f"#{brief.ranking_position} | {brief.event.symbol} | {brief.headline} | {brief.summary} | portfolio match: yes | {brief.explanation.why_it_matters}"
        )


if __name__ == "__main__":
    main()
