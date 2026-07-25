from unittest.mock import patch

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


def test_resolver_returns_none_for_empty_symbol() -> None:
    resolver = TickerResolver()

    with patch(
        "modules.ticker_resolver.get_company_profile"
    ) as mock_get_company_profile:
        company_name = resolver.get_company_name("   ")

    assert company_name is None
    mock_get_company_profile.assert_not_called()


def test_resolver_returns_none_when_name_is_missing() -> None:
    resolver = TickerResolver()

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value={"ticker": "UNKNOWN"},
    ):
        company_name = resolver.get_company_name("UNKNOWN")

    assert company_name is None


def test_clear_cache_forces_new_lookup() -> None:
    resolver = TickerResolver()

    mock_profile = {
        "ticker": "LQDA",
        "name": "Liquidia Corp",
    }

    with patch(
        "modules.ticker_resolver.get_company_profile",
        return_value=mock_profile,
    ) as mock_get_company_profile:
        resolver.get_company_name("LQDA")
        resolver.clear_cache()
        resolver.get_company_name("LQDA")

    assert mock_get_company_profile.call_count == 2


if __name__ == "__main__":
    test_resolver_returns_company_name()
    test_resolver_normalizes_symbol()
    test_resolver_uses_cache()
    test_resolver_returns_none_for_empty_symbol()
    test_resolver_returns_none_when_name_is_missing()
    test_clear_cache_forces_new_lookup()

    print("TickerResolver tests passed.")