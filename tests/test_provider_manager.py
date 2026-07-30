from modules.clinical_trials_provider import ClinicalTrialsProvider
from modules.fda_provider import FDAProvider
from modules.provider_manager import ProviderManager
from modules.ticker_resolver import TickerResolver


def test_provider_manager_builds_default_providers():
    ticker_resolver = TickerResolver()

    manager = ProviderManager(
        ticker_resolver=ticker_resolver,
    )

    providers = manager.build()

    assert len(providers) == 2

    fda_provider = providers[0]
    clinical_trials_provider = providers[1]

    assert isinstance(
        fda_provider,
        FDAProvider,
    )

    assert isinstance(
        clinical_trials_provider,
        ClinicalTrialsProvider,
    )

    assert (
        fda_provider.ticker_resolver
        is ticker_resolver
    )

    assert (
        clinical_trials_provider._ticker_resolver
        is ticker_resolver
    )