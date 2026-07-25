from abc import ABC, abstractmethod

from models.event import Event


class DataProvider(ABC):
    """Base interface for all intelligence providers."""

    @abstractmethod
    def fetch_events(self, symbol: str) -> list[Event]:
        """
        Fetch intelligence events for a stock symbol.

        Args:
            symbol: Stock ticker (e.g. LQDA)

        Returns:
            List of Event objects.
        """
        pass