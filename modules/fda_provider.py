from models.event import Event
from modules.data_provider import DataProvider


class FDAProvider(DataProvider):
    """
    Provider responsible for collecting FDA-related intelligence.

    At this stage the provider is only a skeleton.
    Real FDA integration will be added later.
    """

    def fetch_events(self, symbol: str) -> list[Event]:
        """
        Fetch FDA-related events for the given stock symbol.

        Currently returns an empty list until the real
        FDA integration is implemented.
        """
        return []