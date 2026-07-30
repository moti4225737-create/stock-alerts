from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from models.event import Event


@dataclass(frozen=True, slots=True)
class CompanyIntelligence:
    """
    Aggregated intelligence context for a single company symbol.
    """

    symbol: str
    events: tuple[Event, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        normalized_symbol = self.symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("symbol must not be empty")

        object.__setattr__(
            self,
            "symbol",
            normalized_symbol,
        )

        object.__setattr__(
            self,
            "events",
            tuple(self.events),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )