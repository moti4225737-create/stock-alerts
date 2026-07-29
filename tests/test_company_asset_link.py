import pytest

from models.asset import Asset
from models.asset_kind import AssetKind
from models.company_asset_link import CompanyAssetLink
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


def test_company_asset_link_stores_relationship() -> None:
    company = create_company()
    asset = create_asset()

    link = CompanyAssetLink(
        company=company,
        asset=asset,
        relationship=CompanyAssetRelationship.DEVELOPS,
    )

    assert link.company is company
    assert link.asset is asset

    assert (
        link.relationship
        == CompanyAssetRelationship.DEVELOPS
    )


def test_company_asset_link_is_immutable() -> None:
    link = CompanyAssetLink(
        company=create_company(),
        asset=create_asset(),
        relationship=CompanyAssetRelationship.DEVELOPS,
    )

    with pytest.raises(AttributeError):
        link.relationship = CompanyAssetRelationship.MARKETS


def test_company_asset_link_rejects_invalid_company() -> None:
    with pytest.raises(
        TypeError,
        match="company must be a CompanyIdentity",
    ):
        CompanyAssetLink(
            company="Liquidia Corp",
            asset=create_asset(),
            relationship=CompanyAssetRelationship.DEVELOPS,
        )


def test_company_asset_link_rejects_invalid_asset() -> None:
    with pytest.raises(
        TypeError,
        match="asset must be an Asset",
    ):
        CompanyAssetLink(
            company=create_company(),
            asset="YUTREPIA",
            relationship=CompanyAssetRelationship.DEVELOPS,
        )


def test_company_asset_link_rejects_invalid_relationship() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "relationship must be a "
            "CompanyAssetRelationship"
        ),
    ):
        CompanyAssetLink(
            company=create_company(),
            asset=create_asset(),
            relationship="develops",
        )


if __name__ == "__main__":
    test_company_asset_link_stores_relationship()
    test_company_asset_link_is_immutable()
    test_company_asset_link_rejects_invalid_company()
    test_company_asset_link_rejects_invalid_asset()
    test_company_asset_link_rejects_invalid_relationship()

    print("CompanyAssetLink tests passed.")