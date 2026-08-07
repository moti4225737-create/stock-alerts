from modules.clinical_trials_provider import ClinicalTrialsProvider
from modules.fda_provider import FDAProvider
from modules.provider_manager import ProviderManager
from modules.sec_provider import SECProvider
from modules.ticker_resolver import TickerResolver


def test_provider_manager_builds_default_providers(monkeypatch):
    monkeypatch.setenv(
        "SEC_USER_AGENT",
        "stock-sentinel-tests test@example.com",
    )
    ticker_resolver = TickerResolver()

    manager = ProviderManager(
        ticker_resolver=ticker_resolver,
    )

    providers = manager.build()

    assert len(providers) == 3

    fda_provider = providers[0]
    clinical_trials_provider = providers[1]
    sec_provider = providers[2]

    assert isinstance(fda_provider, FDAProvider)
    assert isinstance(
        clinical_trials_provider,
        ClinicalTrialsProvider,
    )
    assert isinstance(sec_provider, SECProvider)

    assert fda_provider.ticker_resolver is ticker_resolver
    assert (
        clinical_trials_provider._ticker_resolver
        is ticker_resolver
    )


def test_provider_manager_builds_named_providers(monkeypatch):
    monkeypatch.setenv(
        "SEC_USER_AGENT",
        "stock-sentinel-tests test@example.com",
    )
    ticker_resolver = TickerResolver()

    manager = ProviderManager(
        ticker_resolver=ticker_resolver,
    )

    providers = manager.build_named()

    assert tuple(providers) == (
        "FDA",
        "ClinicalTrials.gov",
        "SEC",
    )
    assert isinstance(providers["FDA"], FDAProvider)
    assert isinstance(
        providers["ClinicalTrials.gov"],
        ClinicalTrialsProvider,
    )
    assert isinstance(providers["SEC"], SECProvider)
