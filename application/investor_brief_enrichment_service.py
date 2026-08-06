from collections.abc import Iterable
from typing import Protocol

from models.investor_brief import InvestorBrief


class InvestorBriefEnricher(Protocol):
    def enrich(
        self,
        brief: InvestorBrief,
    ) -> InvestorBrief:
        ...


class InvestorBriefEnrichmentService:
    def __init__(
        self,
        enrichers: Iterable[InvestorBriefEnricher],
    ) -> None:
        self._enrichers = tuple(enrichers)

    def enrich_all(
        self,
        briefs: list[InvestorBrief],
    ) -> tuple[InvestorBrief, ...]:
        enriched_briefs: list[InvestorBrief] = []

        for brief in briefs:
            current = brief

            try:
                for enricher in self._enrichers:
                    current = enricher.enrich(current)
            except Exception:
                current = brief

            enriched_briefs.append(current)

        return tuple(enriched_briefs)
