import unittest

from models.asset import Asset
from models.asset_kind import AssetKind
from models.asset_registry import AssetRegistry


class TestAssetRegistry(unittest.TestCase):
    def test_registered_asset_can_be_found_by_name(self):
        registry = AssetRegistry()

        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
        )

        registry.register(asset)

        found_asset = registry.find_by_name("YUTREPIA")

        self.assertIs(found_asset, asset)

    def test_asset_name_lookup_is_case_insensitive(self):
        registry = AssetRegistry()

        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
        )

        registry.register(asset)

        self.assertIs(
            registry.find_by_name("yutrepia"),
            asset,
        )
        self.assertIs(
            registry.find_by_name("Yutrepia"),
            asset,
        )

    def test_registered_asset_can_be_found_by_alias(self):
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

        self.assertIs(
            registry.find_by_name("LIQ861"),
            asset,
        )
        self.assertIs(
            registry.find_by_name("treprostinil dpi"),
            asset,
        )

    def test_register_rejects_duplicate_asset_name(self):
        registry = AssetRegistry()

        first_asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
        )
        duplicate_asset = Asset(
            name="yutrepia",
            kind=AssetKind.OTHER,
        )

        registry.register(first_asset)

        with self.assertRaises(ValueError):
            registry.register(duplicate_asset)

        self.assertIs(
            registry.find_by_name("YUTREPIA"),
            first_asset,
        )

    def test_register_rejects_name_that_matches_existing_alias(self):
        registry = AssetRegistry()

        first_asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
            aliases=("LIQ861",),
        )
        conflicting_asset = Asset(
            name="liq861",
            kind=AssetKind.OTHER,
        )

        registry.register(first_asset)

        with self.assertRaises(ValueError):
            registry.register(conflicting_asset)

        self.assertIs(
            registry.find_by_name("LIQ861"),
            first_asset,
        )

    def test_register_rejects_alias_that_matches_existing_name(self):
        registry = AssetRegistry()

        first_asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
        )
        conflicting_asset = Asset(
            name="New Drug",
            kind=AssetKind.DRUG,
            aliases=("yutrepia",),
        )

        registry.register(first_asset)

        with self.assertRaises(ValueError):
            registry.register(conflicting_asset)

        self.assertIs(
            registry.find_by_name("YUTREPIA"),
            first_asset,
        )
        self.assertIsNone(
            registry.find_by_name("New Drug"),
        )

    def test_register_rejects_duplicate_identifiers_within_same_asset(self):
        registry = AssetRegistry()

        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
            aliases=(
                "LIQ861",
                "liq861",
            ),
        )

        with self.assertRaises(ValueError):
            registry.register(asset)


if __name__ == "__main__":
    unittest.main()