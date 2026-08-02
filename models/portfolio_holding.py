from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PortfolioHolding:
    symbol: str
    quantity: int
    average_cost: Optional[float] = None
