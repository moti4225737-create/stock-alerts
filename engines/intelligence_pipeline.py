from models.event import Event
from modules.data_provider import DataProvider


class IntelligencePipeline:
    """
    Collects intelligence events from all registered data providers.
    """

    def __init__(self, providers: list[DataProvider]):
        self.providers = providers

    def collect_events(self, symbol: str) -> list[Event]:
        """
        Collect events from every provider.

        Args:
            symbol: Stock ticker.

        Returns:
            Combined list of Event objects.
        """

        events: list[Event] = []

        for provider in self.providers:
            try:
                provider_events = provider.fetch_events(symbol)

                if provider_events:
                    events.extend(provider_events)

            except Exception as error:
                print(
                    f"[WARNING] Provider "
                    f"{provider.__class__.__name__} failed: {error}"
                )

        return events