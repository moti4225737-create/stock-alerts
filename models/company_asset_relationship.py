from enum import Enum


class CompanyAssetRelationship(str, Enum):
    """
    Describes how a company is related to an asset.

    The relationship is intentionally kept separate from AssetKind,
    because AssetKind describes what the asset is, while this enum
    describes what the company does with it.
    """

    OWNS = "owns"
    DEVELOPS = "develops"
    MANUFACTURES = "manufactures"
    MARKETS = "markets"
    LICENSES = "licenses"