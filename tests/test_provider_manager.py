from modules.clinical_trials_provider import ClinicalTrialsProvider
from unittest.mock import Mock

import pytest

import modules.provider_manager as provider_manager_module
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
        source_observation_store=Mock(),
        clinical_trials_page_size=1000,
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
        source_observation_store=Mock(),
        clinical_trials_page_size=1000,
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


def test_provider_manager_injects_source_observation_only_into_clinical_trials(
    monkeypatch,
) -> None:
    ticker_resolver = Mock()
    observation_store = Mock()
    clinical_trials_factory = Mock(return_value=Mock())
    fda_factory = Mock(return_value=Mock())
    sec_factory = Mock(return_value=Mock())
    monkeypatch.setattr(
        provider_manager_module,
        "ClinicalTrialsProvider",
        clinical_trials_factory,
    )
    monkeypatch.setattr(provider_manager_module, "FDAProvider", fda_factory)
    monkeypatch.setattr(provider_manager_module, "SECProvider", sec_factory)

    manager = ProviderManager(
        ticker_resolver=ticker_resolver,
        source_observation_store=observation_store,
        clinical_trials_page_size=1000,
    )

    manager.build_named()

    clinical_trials_factory.assert_called_once_with(
        ticker_resolver=ticker_resolver,
        source_observation_store=observation_store,
        max_events=1000,
    )
    fda_factory.assert_called_once_with(ticker_resolver=ticker_resolver)
    sec_factory.assert_called_once_with()
