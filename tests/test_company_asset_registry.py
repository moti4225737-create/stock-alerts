import pytest

from models.asset import Asset
from models.asset_kind import AssetKind
from models.company_asset_link import CompanyAssetLink
from models.company_asset_registry import CompanyAssetRegistry
from models.company_asset_relationship import (
    CompanyAssetRelationship,
)
from models.company_identity import CompanyIdentity


def create_company() -> CompanyIdentity:
    return CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
        country="US",
        exchange="NASDAQ",
        industry="Pharmaceuticals",
    )


def create_asset() -> Asset:
    return Asset(
        name="YUTREPIA",
        kind=AssetKind.DRUG,
        aliases=("treprostinil inhalation powder",),
    )


def create_link(
    relationship: CompanyAssetRelationship = (
        CompanyAssetRelationship.DEVELOPS
    ),
) -> CompanyAssetLink:
    return CompanyAssetLink(
        company=create_company(),
        asset=create_asset(),
        relationship=relationship,
    )


def test_registers_asset_for_company() -> None:
    registry = CompanyAssetRegistry()
    link = create_link()

    registry.register(link)

    assert registry.get_assets_for_company(
        link.company
    ) == (link.asset,)


def test_registers_company_for_asset() -> None:
    registry = CompanyAssetRegistry()
    link = create_link()

    registry.register(link)

    assert registry.get_companies_for_asset(
        link.asset
    ) == (link.company,)


def test_duplicate_link_is_not_registered_twice() -> None:
    registry = CompanyAssetRegistry()
    link = create_link()

    registry.register(link)
    registry.register(link)

    assert registry.get_assets_for_company(
        link.company
    ) == (link.asset,)

    assert registry.get_companies_for_asset(
        link.asset
    ) == (link.company,)


def test_different_relationships_do_not_duplicate_entities() -> None:
    registry = CompanyAssetRegistry()

    develops_link = create_link(
        CompanyAssetRelationship.DEVELOPS
    )
    markets_link = create_link(
        CompanyAssetRelationship.MARKETS
    )

    registry.register(develops_link)
    registry.register(markets_link)

    assert registry.get_assets_for_company(
        develops_link.company
    ) == (develops_link.asset,)

    assert registry.get_companies_for_asset(
        develops_link.asset
    ) == (develops_link.company,)


def test_returns_all_links_for_company() -> None:
    registry = CompanyAssetRegistry()

    develops_link = create_link(
        CompanyAssetRelationship.DEVELOPS
    )
    markets_link = create_link(
        CompanyAssetRelationship.MARKETS
    )

    registry.register(develops_link)
    registry.register(markets_link)

    assert registry.get_links_for_company(
        develops_link.company
    ) == (
        develops_link,
        markets_link,
    )


def test_returns_all_links_for_asset() -> None:
    registry = CompanyAssetRegistry()

    develops_link = create_link(
        CompanyAssetRelationship.DEVELOPS
    )
    markets_link = create_link(
        CompanyAssetRelationship.MARKETS
    )

    registry.register(develops_link)
    registry.register(markets_link)

    assert registry.get_links_for_asset(
        develops_link.asset
    ) == (
        develops_link,
        markets_link,
    )


def test_register_rejects_invalid_link() -> None:
    registry = CompanyAssetRegistry()

    with pytest.raises(
        TypeError,
        match="link must be a CompanyAssetLink",
    ):
        registry.register("invalid link")


def test_queries_reject_invalid_domain_objects() -> None:
    registry = CompanyAssetRegistry()

    with pytest.raises(
        TypeError,
        match="company must be a CompanyIdentity",
    ):
        registry.get_assets_for_company("LQDA")

    with pytest.raises(
        TypeError,
        match="company must be a CompanyIdentity",
    ):
        registry.get_links_for_company("LQDA")

    with pytest.raises(
        TypeError,
        match="asset must be an Asset",
    ):
        registry.get_companies_for_asset("YUTREPIA")

    with pytest.raises(
        TypeError,
        match="asset must be an Asset",
    ):
        registry.get_links_for_asset("YUTREPIA")