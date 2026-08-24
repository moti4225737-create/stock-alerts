from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from models.portfolio_holding import PortfolioHolding


class SnapshotCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CandidatePortfolioSnapshot:
    positions: tuple[PortfolioHolding, ...]
    source_as_of: datetime
    completeness: SnapshotCompleteness

    @property
    def is_eligible_for_acceptance(self) -> bool:
        return self.completeness is SnapshotCompleteness.COMPLETE
