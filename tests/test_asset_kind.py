import unittest

from models.asset_kind import AssetKind


class TestAssetKind(unittest.TestCase):
    def test_asset_kind_contains_broad_business_categories(self):
        expected_values = {
            "product",
            "service",
            "platform",
            "technology",
            "software",
            "drug",
            "medical_device",
            "program",
            "project",
            "facility",
            "resource",
            "media",
            "financial_product",
            "intellectual_property",
            "other",
        }

        actual_values = {kind.value for kind in AssetKind}

        self.assertEqual(actual_values, expected_values)

    def test_asset_kind_values_are_unique(self):
        values = [kind.value for kind in AssetKind]

        self.assertEqual(len(values), len(set(values)))


if __name__ == "__main__":
    unittest.main()