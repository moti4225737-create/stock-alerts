import unittest

from models.company_identity import CompanyIdentity
from models.company_profile import CompanyProfile


class TestCompanyProfile(unittest.TestCase):
    def test_company_profile_contains_identity_and_intelligence_data(self):
        identity = CompanyIdentity(
            ticker="LQDA",
            company_name="Liquidia Corporation",
            country="US",
            exchange="NASDAQ",
            industry="Pharmaceuticals",
            cik="0001819576",
            website="https://www.liquidia.com",
        )

        profile = CompanyProfile(
            identity=identity,
            aliases=(
                "Liquidia",
                "Liquidia Technologies",
            ),
            former_names=(
                "Liquidia Technologies, Inc.",
            ),
            products=(
                "YUTREPIA",
            ),
            drug_names=(
                "treprostinil",
            ),
            pipeline_assets=(
                "YUTREPIA",
            ),
            therapeutic_areas=(
                "Pulmonary Hypertension",
            ),
            indications=(
                "Pulmonary Arterial Hypertension",
                "Pulmonary Hypertension Associated with Interstitial Lung Disease",
            ),
        )

        self.assertEqual(profile.identity.ticker, "LQDA")
        self.assertEqual(profile.identity.company_name, "Liquidia Corporation")
        self.assertIn("Liquidia", profile.aliases)
        self.assertIn("Liquidia Technologies, Inc.", profile.former_names)
        self.assertIn("YUTREPIA", profile.products)
        self.assertIn("treprostinil", profile.drug_names)
        self.assertIn("YUTREPIA", profile.pipeline_assets)
        self.assertIn("Pulmonary Hypertension", profile.therapeutic_areas)
        self.assertIn(
            "Pulmonary Arterial Hypertension",
            profile.indications,
        )


if __name__ == "__main__":
    unittest.main()