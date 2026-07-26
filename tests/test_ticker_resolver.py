from unittest.mock import patch

from models.company_identity import CompanyIdentity
from modules.ticker_resolver import TickerResolver


def test_resolver_returns_company_name() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "ticker": "LQDA",
        "name": "Liquidia Corp",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        company_name = resolver.get_company_name("LQDA")

    assert company_name == "Liquidia Corp"
    mock_get_company_profile.assert_called_once_with("LQDA")


def test_resolver_normalizes_symbol() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "ticker": "LQDA",
        "name": "Liquidia Corp",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        company_name = resolver.get_company_name("  lqda  ")

    assert company_name == "Liquidia Corp"
    mock_get_company_profile.assert_called_once_with("LQDA")


def test_resolver_uses_cache() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "ticker": "LQDA",
        "name": "Liquidia Corp",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        first_result = resolver.get_company_name("LQDA")
        second_result = resolver.get_company_name("lqda")

    assert first_result == "Liquidia Corp"
    assert second_result == "Liquidia Corp"
    mock_get_company_profile.assert_called_once_with("LQDA")


def test_resolver_returns_company_identity() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "ticker": "LQDA",
        "name": "Liquidia Corp",
        "country": "US",
        "exchange": "NASDAQ NMS - GLOBAL MARKET",
        "finnhubIndustry": "Pharmaceuticals",
        "weburl": "https://www.liquidia.com/",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        identity = resolver.get_company_identity("LQDA")

    assert identity == CompanyIdentity(
        ticker="LQDA",
        company_name="Liquidia Corp",
        country="US",
        exchange="NASDAQ NMS - GLOBAL MARKET",
        industry="Pharmaceuticals",
        cik=None,
        website="https://www.liquidia.com/",
    )
    mock_get_company_profile.assert_called_once_with("LQDA")


def test_identity_normalizes_symbol() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "name": "Liquidia Corp",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        identity = resolver.get_company_identity("  lqda  ")

    assert identity is not None
    assert identity.ticker == "LQDA"
    mock_get_company_profile.assert_called_once_with("LQDA")


def test_identity_cleans_optional_fields() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "name": " Liquidia Corp ",
        "country": " ",
        "exchange": None,
        "finnhubIndustry": 123,
        "weburl": " https://www.liquidia.com/ ",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ):
        identity = resolver.get_company_identity("LQDA")

    assert identity is not None
    assert identity.company_name == "Liquidia Corp"
    assert identity.country is None
    assert identity.exchange is None
    assert identity.industry is None
    assert identity.website == "https://www.liquidia.com/"


def test_name_and_identity_share_profile_cache() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "name": "Liquidia Corp",
        "country": "US",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        company_name = resolver.get_company_name("LQDA")
        identity = resolver.get_company_identity("LQDA")

    assert company_name == "Liquidia Corp"
    assert identity is not None
    assert identity.company_name == "Liquidia Corp"
    assert identity.country == "US"
    mock_get_company_profile.assert_called_once_with("LQDA")


def test_identity_uses_cache() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "name": "Liquidia Corp",
        "country": "US",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        first_identity = resolver.get_company_identity("LQDA")
        second_identity = resolver.get_company_identity("lqda")

    assert first_identity is not None
    assert second_identity is first_identity
    mock_get_company_profile.assert_called_once_with("LQDA")


def test_resolver_returns_none_for_empty_symbol() -> None:
    resolver = TickerResolver()

    with patch(
        "modules.ticker_resolver.get_company_profile"
    ) as mock_get_company_profile:
        company_name = resolver.get_company_name("   ")
        identity = resolver.get_company_identity("   ")

    assert company_name is None
    assert identity is None
    mock_get_company_profile.assert_not_called()


def test_resolver_returns_none_when_name_is_missing() -> None:
    resolver = TickerResolver()

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value={"ticker": "UNKNOWN"},
    ):
        company_name = resolver.get_company_name("UNKNOWN")

    assert company_name is None


def test_identity_returns_none_when_name_is_missing() -> None:
    resolver = TickerResolver()

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value={
            "ticker": "UNKNOWN",
            "country": "US",
        },
    ):
        identity = resolver.get_company_identity("UNKNOWN")

    assert identity is None


def test_resolver_returns_none_when_profile_is_empty() -> None:
    resolver = TickerResolver()

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value={},
    ):
        company_name = resolver.get_company_name("UNKNOWN")
        identity = resolver.get_company_identity("UNKNOWN")

    assert company_name is None
    assert identity is None


def test_clear_cache_forces_new_lookup() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "ticker": "LQDA",
        "name": "Liquidia Corp",
        "country": "US",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        resolver.get_company_name("LQDA")
        resolver.get_company_identity("LQDA")

        resolver.clear_cache()

        resolver.get_company_identity("LQDA")

    assert mock_get_company_profile.call_count == 2


def test_prepare_company_search_name_removes_corp() -> None:
    result = TickerResolver.prepare_company_search_name(
        "Liquidia Corp"
    )

    assert result == "Liquidia"


def test_prepare_company_search_name_removes_inc_period() -> None:
    result = TickerResolver.prepare_company_search_name(
        "Example Biotech Inc."
    )

    assert result == "Example Biotech"


def test_prepare_company_search_name_removes_corporation() -> None:
    result = TickerResolver.prepare_company_search_name(
        "Microsoft Corporation"
    )

    assert result == "Microsoft"


def test_prepare_company_search_name_is_case_insensitive() -> None:
    result = TickerResolver.prepare_company_search_name(
        "Example Biotech INC."
    )

    assert result == "Example Biotech"


def test_prepare_company_search_name_strips_whitespace() -> None:
    result = TickerResolver.prepare_company_search_name(
        "  Liquidia Corp  "
    )

    assert result == "Liquidia"


def test_prepare_company_search_name_keeps_name_without_suffix() -> None:
    result = TickerResolver.prepare_company_search_name(
        "Liquidia Technologies"
    )

    assert result == "Liquidia Technologies"


def test_prepare_company_search_name_handles_empty_name() -> None:
    result = TickerResolver.prepare_company_search_name("   ")

    assert result == ""


if __name__ == "__main__":
    test_resolver_returns_company_name()
    test_resolver_normalizes_symbol()
    test_resolver_uses_cache()
    test_resolver_returns_company_identity()
    test_identity_normalizes_symbol()
    test_identity_cleans_optional_fields()
    test_name_and_identity_share_profile_cache()
    test_identity_uses_cache()
    test_resolver_returns_none_for_empty_symbol()
    test_resolver_returns_none_when_name_is_missing()
    test_identity_returns_none_when_name_is_missing()
    test_resolver_returns_none_when_profile_is_empty()
    test_clear_cache_forces_new_lookup()
    test_prepare_company_search_name_removes_corp()
    test_prepare_company_search_name_removes_inc_period()
    test_prepare_company_search_name_removes_corporation()
    test_prepare_company_search_name_is_case_insensitive()
    test_prepare_company_search_name_strips_whitespace()
    test_prepare_company_search_name_keeps_name_without_suffix()
    test_prepare_company_search_name_handles_empty_name()

    print("TickerResolver tests passed.")