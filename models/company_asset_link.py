from dataclasses import dataclass

from models.asset import Asset
from models.company_asset_relationship import (
    CompanyAssetRelationship,
)
from models.company_identity import CompanyIdentity


@dataclass(frozen=True, slots=True)
class CompanyAssetLink:
    """
    Represents a relationship between a public company and one
    of its assets.

    Examples include a company developing a drug, manufacturing
    a device, marketing a product, or licensing technology.
    """

    company: CompanyIdentity
    asset: Asset
    relationship: CompanyAssetRelationship

    def __post_init__(self) -> None:
        if not isinstance(self.company, CompanyIdentity):
            raise TypeError(
                "company must be a CompanyIdentity"
            )

        if not isinstance(self.asset, Asset):
            raise TypeError(
                "asset must be an Asset"
            )

        if not isinstance(
            self.relationship,
            CompanyAssetRelationship,
        ):
            raise TypeError(
                "relationship must be a "
                "CompanyAssetRelationship"
            )