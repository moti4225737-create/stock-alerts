from typing import Dict, Optional

from modules.finnhub_client import get_company_profile


class TickerResolver:
    """
    Resolve stock ticker symbols into company names.

    Company names are retrieved from Finnhub and cached in memory
    to avoid repeated API requests during the same program run.
    """

    def __init__(self) -> None:
        self._company_name_cache: Dict[str, str] = {}

    def get_company_name(self, symbol: str) -> Optional[str]:
        """
        Return the company name associated with a ticker symbol.

        Returns None when the symbol is empty, Finnhub does not return
        a company name, or the API request fails.
        """
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            return None

        cached_name = self._company_name_cache.get(normalized_symbol)

        if cached_name is not None:
            return cached_name

        try:
            profile = get_company_profile(normalized_symbol)
        except (RuntimeError, ValueError, OSError):
            return None

        company_name = profile.get("name")

        if not isinstance(company_name, str):
            return None

        company_name = company_name.strip()

        if not company_name:
            return None

        self._company_name_cache[normalized_symbol] = company_name

        return company_name

    def clear_cache(self) -> None:
        """
        Clear all company names currently stored in memory.
        """
        self._company_name_cache.clear()