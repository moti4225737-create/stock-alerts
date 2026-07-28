import unittest

from models.asset import Asset
from models.asset_kind import AssetKind
from models.asset_registry import AssetRegistry
from models.asset_resolver import AssetResolver
from tests.test_support.fake_asset_provider import FakeAssetProvider


class TestAssetResolver(unittest.TestCase):
    def test_resolve_returns_registered_asset_by_name(self):
        registry = AssetRegistry()

        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
            aliases=(
                "LIQ861",
                "Treprostinil DPI",
            ),
        )

        registry.register(asset)

        resolver = AssetResolver(registry)

        resolved_asset = resolver.resolve("YUTREPIA")

        self.assertIs(resolved_asset, asset)

    def test_resolve_returns_none_for_unknown_identifier(self):
        registry = AssetRegistry()

        resolver = AssetResolver(registry)

        resolved_asset = resolver.resolve("UNKNOWN-ASSET")

        self.assertIsNone(resolved_asset)

    def test_resolve_returns_asset_from_provider_when_registry_misses(self):
        registry = AssetRegistry()

        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
        )

        provider = FakeAssetProvider(asset)

        resolver = AssetResolver(
            registry,
            providers=[provider],
        )

        resolved_asset = resolver.resolve("LIQ861")

        self.assertIs(resolved_asset, asset)

    def test_resolve_registers_asset_returned_by_provider(self):
        registry = AssetRegistry()

        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
            aliases=(
                "LIQ861",
                "Treprostinil DPI",
            ),
        )

        provider = FakeAssetProvider(asset)

        resolver = AssetResolver(
            registry,
            providers=[provider],
        )

        resolved_asset = resolver.resolve("LIQ861")

        self.assertIs(resolved_asset, asset)
        self.assertIs(
            registry.find_by_name("YUTREPIA"),
            asset,
        )
        self.assertIs(
            registry.find_by_name("Treprostinil DPI"),
            asset,
        )

    def test_resolve_uses_registry_after_provider_asset_is_registered(self):
        registry = AssetRegistry()

        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
            aliases=("LIQ861",),
        )

        provider = FakeAssetProvider(asset)

        resolver = AssetResolver(
            registry,
            providers=[provider],
        )

        first_result = resolver.resolve("LIQ861")
        second_result = resolver.resolve("YUTREPIA")

        self.assertIs(first_result, asset)
        self.assertIs(second_result, asset)
        self.assertEqual(provider.call_count, 1)


if __name__ == "__main__":
    unittest.main()