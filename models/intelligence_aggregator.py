from collections import defaultdict

from models.company_intelligence import CompanyIntelligence
from models.event import Event


class IntelligenceAggregator:
    """
    Aggregate normalized intelligence events by company symbol.
    """

    def aggregate(
        self,
        events: list[Event],
    ) -> dict[str, CompanyIntelligence]:
        """
        Return company intelligence grouped by normalized symbol.
        """
        grouped_events: defaultdict[str, list[Event]] = defaultdict(list)

        for event in events:
            normalized_symbol = event.symbol.strip().upper()

            if not normalized_symbol:
                continue

            grouped_events[normalized_symbol].append(event)

        return {
            symbol: CompanyIntelligence(
                symbol=symbol,
                events=company_events,
            )
            for symbol, company_events in grouped_events.items()
        }