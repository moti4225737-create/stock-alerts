from dataclasses import dataclass
from enum import Enum


class ImportanceLevel(str, Enum):
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    MATERIAL_FILING = "material_filing"
    CORPORATE_DISCLOSURE = "corporate_disclosure"


@dataclass(frozen=True, slots=True)
class InvestorIntelligenceCard:
    importance_level: ImportanceLevel
    event_category: EventCategory
    title: str
    symbol: str
    summary: str
    why_it_matters: str
    portfolio_impact: str
    points_to_watch: tuple[str, ...]
    source: str
    source_url: str | None
    published_at: str