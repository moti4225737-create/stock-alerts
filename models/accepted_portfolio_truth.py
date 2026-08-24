from dataclasses import dataclass
from datetime import datetime

from models.portfolio_holding import PortfolioHolding


@dataclass(frozen=True)
class AcceptedPortfolioTruth:
    positions: tuple[PortfolioHolding, ...]
    source_as_of: datetime
    accepted_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "positions", tuple(self.positions))
        self._validate_aware_datetime("source_as_of", self.source_as_of)
        self._validate_aware_datetime("accepted_at", self.accepted_at)

    @staticmethod
    def _validate_aware_datetime(name: str, value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{name} must be timezone-aware")
