from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CompanyIdentity:
    """
    Canonical identity of a public company.

    This object can be shared between data providers such as
    SEC, FDA, ClinicalTrials and News.
    """

    ticker: str
    company_name: str
    country: Optional[str] = None
    exchange: Optional[str] = None
    industry: Optional[str] = None
    cik: Optional[str] = None
    website: Optional[str] = None