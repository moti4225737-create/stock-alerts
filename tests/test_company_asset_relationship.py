from models.company_asset_relationship import (
    CompanyAssetRelationship,
)


def test_relationship_values() -> None:
    assert (
        CompanyAssetRelationship.OWNS.value
        == "owns"
    )

    assert (
        CompanyAssetRelationship.DEVELOPS.value
        == "develops"
    )

    assert (
        CompanyAssetRelationship.MANUFACTURES.value
        == "manufactures"
    )

    assert (
        CompanyAssetRelationship.MARKETS.value
        == "markets"
    )

    assert (
        CompanyAssetRelationship.LICENSES.value
        == "licenses"
    )


if __name__ == "__main__":
    test_relationship_values()

    print(
        "CompanyAssetRelationship tests passed."
    )