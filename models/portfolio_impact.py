from dataclasses import dataclass

from models.event import Event
from models.portfolio_holding import PortfolioHolding


@dataclass(frozen=True)
class PortfolioImpact:
    holding: PortfolioHolding
    event: Event
    matches_portfolio: bool
