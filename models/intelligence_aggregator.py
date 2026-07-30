from collections import defaultdict

from models.event import Event


class IntelligenceAggregator:
    """
    Group normalized intelligence events by stock symbol.
    """

    def aggregate(
        self,
        events: list[Event],
    ) -> dict[str, list[Event]]:
        """
        Return events grouped by their normalized symbol.
        """
        grouped_events: defaultdict[str, list[Event]] = defaultdict(list)

        for event in events:
            normalized_symbol = event.symbol.strip().upper()

            if not normalized_symbol:
                continue

            grouped_events[normalized_symbol].append(event)

        return dict(grouped_events)