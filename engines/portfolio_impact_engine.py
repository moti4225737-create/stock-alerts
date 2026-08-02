from models.event import Event
from models.portfolio import Portfolio
from models.portfolio_impact import PortfolioImpact


class PortfolioImpactEngine:
    def analyze(self, portfolio: Portfolio, events: list[Event]) -> list[PortfolioImpact]:
        impacts: list[PortfolioImpact] = []

        for event in events:
            holding = portfolio.get(event.symbol)
            if holding is None:
                continue

            impacts.append(
                PortfolioImpact(
                    holding=holding,
                    event=event,
                    matches_portfolio=True,
                )
            )

        return impacts
