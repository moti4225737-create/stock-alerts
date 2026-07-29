from models.asset import Asset
from models.company_asset_link import CompanyAssetLink
from models.company_identity import CompanyIdentity


class CompanyAssetRegistry:
    """
    Stores relationships between companies and their assets.

    The registry acts as an in-memory knowledge base while
    preserving the complete CompanyAssetLink relationship.
    """

    def __init__(self) -> None:
        self._links: list[CompanyAssetLink] = []

    def register(self, link: CompanyAssetLink) -> None:
        """
        Register a relationship between a company and an asset.

        Registering an identical link more than once has no effect.
        """
        if not isinstance(link, CompanyAssetLink):
            raise TypeError(
                "link must be a CompanyAssetLink"
            )

        if link not in self._links:
            self._links.append(link)

    def get_assets_for_company(
        self,
        company: CompanyIdentity,
    ) -> tuple[Asset, ...]:
        """
        Return the unique assets associated with a company.
        """
        self._validate_company(company)

        assets: list[Asset] = []

        for link in self._links:
            if (
                link.company == company
                and link.asset not in assets
            ):
                assets.append(link.asset)

        return tuple(assets)

    def get_companies_for_asset(
        self,
        asset: Asset,
    ) -> tuple[CompanyIdentity, ...]:
        """
        Return the unique companies associated with an asset.
        """
        self._validate_asset(asset)

        companies: list[CompanyIdentity] = []

        for link in self._links:
            if (
                link.asset == asset
                and link.company not in companies
            ):
                companies.append(link.company)

        return tuple(companies)

    def get_links_for_company(
        self,
        company: CompanyIdentity,
    ) -> tuple[CompanyAssetLink, ...]:
        """
        Return all registered links for a company.
        """
        self._validate_company(company)

        return tuple(
            link
            for link in self._links
            if link.company == company
        )

    def get_links_for_asset(
        self,
        asset: Asset,
    ) -> tuple[CompanyAssetLink, ...]:
        """
        Return all registered links for an asset.
        """
        self._validate_asset(asset)

        return tuple(
            link
            for link in self._links
            if link.asset == asset
        )

    @staticmethod
    def _validate_company(
        company: CompanyIdentity,
    ) -> None:
        if not isinstance(company, CompanyIdentity):
            raise TypeError(
                "company must be a CompanyIdentity"
            )

    @staticmethod
    def _validate_asset(asset: Asset) -> None:
        if not isinstance(asset, Asset):
            raise TypeError(
                "asset must be an Asset"
            )