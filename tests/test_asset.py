import unittest
from dataclasses import FrozenInstanceError

from models.asset import Asset
from models.asset_kind import AssetKind


class TestAsset(unittest.TestCase):
    def test_asset_contains_core_investment_information(self):
        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
            subtype="inhaled prostacyclin therapy",
            aliases=(
                "LIQ861",
            ),
            status="Late-stage development",
            metadata={
                "generic_name": "treprostinil",
                "route": "dry powder inhalation",
            },
        )

        self.assertEqual(asset.name, "YUTREPIA")
        self.assertIs(asset.kind, AssetKind.DRUG)
        self.assertEqual(
            asset.subtype,
            "inhaled prostacyclin therapy",
        )
        self.assertIn("LIQ861", asset.aliases)
        self.assertEqual(asset.status, "Late-stage development")
        self.assertEqual(
            asset.metadata["generic_name"],
            "treprostinil",
        )
        self.assertEqual(
            asset.metadata["route"],
            "dry powder inhalation",
        )

    def test_asset_uses_optional_defaults(self):
        asset = Asset(
            name="CUDA",
            kind=AssetKind.SOFTWARE,
        )

        self.assertIsNone(asset.subtype)
        self.assertEqual(asset.aliases, ())
        self.assertIsNone(asset.status)
        self.assertEqual(dict(asset.metadata), {})

    def test_unknown_asset_can_be_stored_without_being_discarded(self):
        asset = Asset(
            name="NovaX-27",
            kind=AssetKind.OTHER,
        )

        self.assertEqual(asset.name, "NovaX-27")
        self.assertIs(asset.kind, AssetKind.OTHER)
        self.assertIsNone(asset.subtype)

    def test_asset_fields_are_immutable(self):
        asset = Asset(
            name="Blackwell",
            kind=AssetKind.PLATFORM,
        )

        with self.assertRaises(FrozenInstanceError):
            asset.name = "Other"

    def test_asset_metadata_is_immutable_and_defensively_copied(self):
        source_metadata = {
            "generic_name": "treprostinil",
        }

        asset = Asset(
            name="YUTREPIA",
            kind=AssetKind.DRUG,
            metadata=source_metadata,
        )

        source_metadata["generic_name"] = "changed externally"

        self.assertEqual(
            asset.metadata["generic_name"],
            "treprostinil",
        )

        with self.assertRaises(TypeError):
            asset.metadata["generic_name"] = "changed internally"


if __name__ == "__main__":
    unittest.main()