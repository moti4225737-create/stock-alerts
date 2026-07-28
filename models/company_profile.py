from dataclasses import dataclass

from models.company_identity import CompanyIdentity


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    """
    Represents enriched investment intelligence about a company.

    CompanyIdentity contains the company's canonical identifying data.
    CompanyProfile extends that identity with products, assets, aliases,
    therapeutic areas, and indications used for entity resolution.
    """

    identity: CompanyIdentity
    aliases: tuple[str, ...]
    former_names: tuple[str, ...]
    products: tuple[str, ...]
    drug_names: tuple[str, ...]
    pipeline_assets: tuple[str, ...]
    therapeutic_areas: tuple[str, ...]
    indications: tuple[str, ...]