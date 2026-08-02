from dataclasses import dataclass

from models.event import Event
from models.explanation import Explanation
from models.portfolio_impact import PortfolioImpact


@dataclass(frozen=True)
class InvestorBrief:
    event: Event
    ranking_position: int
    portfolio_impact: PortfolioImpact
    headline: str
    summary: str
    explanation: Explanation
