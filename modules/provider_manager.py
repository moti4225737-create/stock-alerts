from modules.clinical_trials_provider import ClinicalTrialsProvider
from modules.data_provider import DataProvider
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
    ) -> None:
        self._ticker_resolver = ticker_resolver

    def build_named(self) -> dict[str, DataProvider]:
        """
        Create the default provider collection keyed by source name.
        """
        return {
            "FDA": FDAProvider(
                ticker_resolver=self._ticker_resolver,
            ),
            "ClinicalTrials.gov": ClinicalTrialsProvider(
                ticker_resolver=self._ticker_resolver,
            ),
            "SEC": SECProvider(),
        }

    def build(self) -> list[DataProvider]:
        """
        Create the default provider collection.
        """
        return list(self.build_named().values())
