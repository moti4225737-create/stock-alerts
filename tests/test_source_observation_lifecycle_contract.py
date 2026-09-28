import importlib


def test_managed_source_observation_lifecycle_contract_exists():
    """
    O22 contract.

    Providers participating in Source Observation must expose one shared
    acknowledgement lifecycle contract without expanding the minimal
    DataProvider acquisition contract.
    """
    module = importlib.import_module("modules.source_observation_lifecycle")

    contract = getattr(module, "ManagedSourceObservationProvider")

    assert hasattr(contract, "acknowledge_pending")

def test_all_source_observation_providers_use_shared_lifecycle_contract():
    from modules.clinical_trials_provider import ClinicalTrialsProvider
    from modules.fda_provider import FDAProvider
    from modules.sec_provider import SECProvider
    from modules.source_observation_lifecycle import (
        ManagedSourceObservationProvider,
    )

    providers = (
        ClinicalTrialsProvider,
        FDAProvider,
        SECProvider,
    )

    for provider in providers:
        assert issubclass(provider, ManagedSourceObservationProvider)
