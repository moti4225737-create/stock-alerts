from modules.clinical_trials_provider import ClinicalTrialsProvider
from modules.data_provider import DataProvider
from collections.abc import Callable
from datetime import datetime
from modules.fda_provider import FDAProvider
from modules.sec_provider import SECProvider
from modules.ticker_resolver import TickerResolver


class ProviderManager:
    """
    Build the default set of intelligence providers.

    The manager centralizes provider construction so runtime
    configuration does not remain inside main.py.
    """

    def __init__(
        self,
        ticker_resolver: TickerResolver,
        source_observation_store: object,
        clinical_trials_page_size: int,
        time_zero_for: Callable[[str], datetime | None] | None = None,
    ) -> None:
        self._ticker_resolver = ticker_resolver
        self._time_zero_for = time_zero_for
        self._source_observation_store = source_observation_store
        self._clinical_trials_page_size = clinical_trials_page_size

    def build_named(self) -> dict[str, DataProvider]:
        """
        Create the default provider collection keyed by source name.
        """
        # Preserve legacy construction when no Opening context is supplied.
        relay = (
            {"time_zero_for": self._time_zero_for}
            if self._time_zero_for is not None else {}
        )
        observation = (
            {"source_observation_store": self._source_observation_store}
            if self._time_zero_for is not None else {}
        )
        return {
            "FDA": FDAProvider(
                ticker_resolver=self._ticker_resolver,
                **relay,
                **observation,
            ),
            "ClinicalTrials.gov": ClinicalTrialsProvider(
                **relay,
                ticker_resolver=self._ticker_resolver,
                source_observation_store=self._source_observation_store,
                max_events=self._clinical_trials_page_size,
            ),
            "SEC": SECProvider(**relay, **observation),
        }

    def build(self) -> list[DataProvider]:
        """
        Create the default provider collection.
        """
        return list(self.build_named().values())
