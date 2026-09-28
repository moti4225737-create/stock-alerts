from engines.scoring_engine import ScoringEngine
from models.event import Event
from modules.data_provider import DataProvider


class IntelligencePipeline:
    """
    Collects and scores intelligence events from all registered data providers.
    """

    def __init__(
        self,
        providers: list[DataProvider],
        scoring_engine: ScoringEngine | None = None,
    ):
        self._collection_failures: list[Exception] = []
        self.providers = providers
        self.scoring_engine = scoring_engine or ScoringEngine()

    def collect_events(self, symbol: str) -> list[Event]:
        """
        Collect and score events from every provider.

        Args:
            symbol: Stock ticker.

        Returns:
            Combined list of scored Event objects.
        """

        events: list[Event] = []

        for provider in self.providers:
            try:
                provider_events = provider.fetch_events(symbol)

                if provider_events:
                    for event in provider_events:
                        event.importance = self.scoring_engine.score(event)

                    events.extend(provider_events)

            except Exception as error:
                self._collection_failures.append(error)
                print(
                    f"[WARNING] Provider "
                    f"{provider.__class__.__name__} failed: {error}"
                )

        return events

    def raise_if_collection_failed(self) -> None:
        if self._collection_failures:
            raise RuntimeError(
                f"{len(self._collection_failures)} collection failure(s) in source attempt"
            ) from self._collection_failures[0]