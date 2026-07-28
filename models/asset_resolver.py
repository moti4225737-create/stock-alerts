from models.asset import Asset
from models.asset_registry import AssetRegistry


class AssetResolver:
    def __init__(
        self,
        registry: AssetRegistry,
        providers: list | None = None,
    ):
        self._registry = registry
        self._providers = providers or []

    def resolve(self, identifier: str) -> Asset | None:
        registered_asset = self._registry.find_by_name(identifier)

        if registered_asset is not None:
            return registered_asset

        for provider in self._providers:
            asset = provider.find(identifier)

            if asset is not None:
                self._registry.register(asset)
                return asset

        return None