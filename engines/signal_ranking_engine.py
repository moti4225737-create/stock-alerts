from models.event import Event


class SignalRankingEngine:
    """
    Rank events by importance in descending order.
    """

    def rank(self, events: list[Event]) -> list[Event]:
        """
        Return a new list of events ordered by importance descending.
        When importance ties, newer published_at values rank first.
        """
        return sorted(
            events,
            key=lambda event: (event.importance, event.published_at),
            reverse=True,
        )
