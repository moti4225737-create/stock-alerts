from typing import Dict, Optional

from models.company_identity import CompanyIdentity
from modules.finnhub_client import get_company_profile


class TickerResolver:
    """
    Resolve stock ticker symbols into company information.

    Company profiles are retrieved from Finnhub and cached in memory
    to avoid repeated API requests during the same program run.
    """

    def __init__(self) -> None:
        self._profile_cache: Dict[str, dict] = {}
        self._company_name_cache: Dict[str, str] = {}
        self._identity_cache: Dict[str, CompanyIdentity] = {}

    def get_company_name(self, symbol: str) -> Optional[str]:
        """
        Return the company name associated with a ticker symbol.

        Returns None when the symbol is empty, Finnhub does not return
        a company name, or the API request fails.
        """
        normalized_symbol = self._normalize_symbol(symbol)

        if normalized_symbol is None:
            return None

        cached_name = self._company_name_cache.get(normalized_symbol)

        if cached_name is not None:
            return cached_name

        profile = self._get_profile(normalized_symbol)

        if profile is None:
            return None

        company_name = self._clean_optional_string(
            profile.get("name")
        )

        if company_name is None:
            return None

        self._company_name_cache[normalized_symbol] = company_name

        return company_name

    def get_company_identity(
        self,
        symbol: str,
    ) -> Optional[CompanyIdentity]:
        """
        Return a structured company identity for a ticker symbol.

        The identity currently includes information available from
        Finnhub. The CIK field remains None until an SEC identity
        source is connected.
        """
        normalized_symbol = self._normalize_symbol(symbol)

        if normalized_symbol is None:
            return None

        cached_identity = self._identity_cache.get(
            normalized_symbol
        )

        if cached_identity is not None:
            return cached_identity

        profile = self._get_profile(normalized_symbol)

        if profile is None:
            return None

        company_name = self._clean_optional_string(
            profile.get("name")
        )

        if company_name is None:
            return None

        identity = CompanyIdentity(
            ticker=normalized_symbol,
            company_name=company_name,
            country=self._clean_optional_string(
                profile.get("country")
            ),
            exchange=self._clean_optional_string(
                profile.get("exchange")
            ),
            industry=self._clean_optional_string(
                profile.get("finnhubIndustry")
            ),
            cik=None,
            website=self._clean_optional_string(
                profile.get("weburl")
            ),
        )

        self._company_name_cache[normalized_symbol] = (
            company_name
        )
        self._identity_cache[normalized_symbol] = identity

        return identity

    def clear_cache(self) -> None:
        """
        Clear all company information currently stored in memory.
        """
        self._profile_cache.clear()
        self._company_name_cache.clear()
        self._identity_cache.clear()

    def _get_profile(
        self,
        normalized_symbol: str,
    ) -> Optional[dict]:
        """
        Return a Finnhub company profile, using the cache when possible.
        """
        cached_profile = self._profile_cache.get(
            normalized_symbol
        )

        if cached_profile is not None:
            return cached_profile

        try:
            profile = get_company_profile(normalized_symbol)
        except (RuntimeError, ValueError, OSError):
            return None

        if not isinstance(profile, dict) or not profile:
            return None

        self._profile_cache[normalized_symbol] = profile

        return profile

    @staticmethod
    def prepare_company_search_name(
        company_name: str,
    ) -> str:
        """
        Prepare a company name for searches against external
        intelligence providers.

        Common corporate suffixes are removed because many
        external datasets store operational company names
        instead of their full legal names.
        """
        cleaned_name = company_name.strip()

        suffixes = (
            " Corporation",
            " Incorporated",
            " Corp.",
            " Corp",
            " Inc.",
            " Inc",
            " Ltd.",
            " Ltd",
            " Limited",
            " PLC",
            " N.V.",
            " S.A.",
        )

        for suffix in suffixes:
            if cleaned_name.lower().endswith(
                suffix.lower()
            ):
                cleaned_name = cleaned_name[
                    :-len(suffix)
                ].strip()
                break

        return cleaned_name

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> Optional[str]:
        """
        Normalize a ticker symbol or return None when it is empty.
        """
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            return None

        return normalized_symbol

    @staticmethod
    def _clean_optional_string(
        value: object,
    ) -> Optional[str]:
        """
        Return a stripped string or None for invalid and empty values.
        """
        if not isinstance(value, str):
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            return None

        return cleaned_value