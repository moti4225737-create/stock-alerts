from datetime import date
from unittest.mock import Mock

from models.asset import Asset
from models.asset_kind import AssetKind
from models.asset_registry import AssetRegistry
from models.company_asset_registry import CompanyAssetRegistry
from models.company_asset_relationship import (
    CompanyAssetRelationship,
)
from models.company_identity import CompanyIdentity
from modules.clinical_trials_provider import (
    ClinicalTrialsProvider,
)


TEST_TODAY = date(2026, 7, 29)
RECENT_DATE = "2026-07-20"


def create_study(
    intervention_name: str = "YUTREPIA",
    other_names: list[str] | None = None,
) -> dict:
    if other_names is None:
        other_names = [
            "treprostinil inhalation powder",
        ]

    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT01234567",
                "briefTitle": "A Study of YUTREPIA",
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "studyFirstPostDateStruct": {
                    "date": RECENT_DATE,
                },
            },
            "armsInterventionsModule": {
                "interventions": [
                    {
                        "type": "DRUG",
                        "name": intervention_name,
                        "otherNames": other_names,
                    }
                ]
            },
        }
    }


def create_identity() -> CompanyIdentity:
    return CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
    )


def create_ticker_resolver(
    identity: CompanyIdentity,
) -> Mock:
    ticker_resolver = Mock()
    ticker_resolver.get_company_identity.return_value = identity
    ticker_resolver.prepare_company_search_name.return_value = (
        "Liquidia"
    )

    return ticker_resolver


def test_registers_clinical_trial_drug_for_company() -> None:
    identity = create_identity()
    ticker_resolver = create_ticker_resolver(identity)

    client = Mock()
    client.search_studies.return_value = [
        create_study()
    ]

    asset_registry = AssetRegistry()
    company_asset_registry = CompanyAssetRegistry()

    provider = ClinicalTrialsProvider(
        client=client,
        ticker_resolver=ticker_resolver,
        asset_registry=asset_registry,
        company_asset_registry=company_asset_registry,
        today_provider=lambda: TEST_TODAY,
    )

    events = provider.fetch_events("LQDA")

    registered_asset = asset_registry.find_by_name(
        "YUTREPIA"
    )

    assert len(events) == 1
    assert registered_asset is not None
    assert registered_asset.kind == AssetKind.DRUG
    assert registered_asset.aliases == (
        "treprostinil inhalation powder",
    )

    assert company_asset_registry.get_assets_for_company(
        identity
    ) == (registered_asset,)

    assert company_asset_registry.get_links_for_company(
        identity
    )[0].relationship == (
        CompanyAssetRelationship.DEVELOPS
    )


def test_reuses_existing_canonical_asset_found_by_alias() -> None:
    identity = create_identity()
    ticker_resolver = create_ticker_resolver(identity)

    existing_asset = Asset(
        name="YUTREPIA",
        kind=AssetKind.DRUG,
        aliases=(
            "treprostinil inhalation powder",
        ),
    )

    asset_registry = AssetRegistry()
    asset_registry.register(existing_asset)

    company_asset_registry = CompanyAssetRegistry()

    client = Mock()
    client.search_studies.return_value = [
        create_study(
            intervention_name=(
                "treprostinil inhalation powder"
            ),
            other_names=[
                "YUTREPIA",
            ],
        )
    ]

    provider = ClinicalTrialsProvider(
        client=client,
        ticker_resolver=ticker_resolver,
        asset_registry=asset_registry,
        company_asset_registry=company_asset_registry,
        today_provider=lambda: TEST_TODAY,
    )

    events = provider.fetch_events("LQDA")

    asset_found_by_name = asset_registry.find_by_name(
        "YUTREPIA"
    )
    asset_found_by_alias = asset_registry.find_by_name(
        "treprostinil inhalation powder"
    )

    linked_assets = (
        company_asset_registry.get_assets_for_company(
            identity
        )
    )

    assert len(events) == 1
    assert asset_found_by_name is existing_asset
    assert asset_found_by_alias is existing_asset
    assert linked_assets == (existing_asset,)
    assert linked_assets[0] is existing_asset