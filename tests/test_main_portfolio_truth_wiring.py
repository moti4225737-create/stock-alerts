from unittest.mock import Mock

import pytest

import main
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from modules.file_portfolio_truth_store import PortfolioTruthStorageError


def _prepare_main(
    monkeypatch,
    *,
    portfolio,
    restore_result=False,
    refresh_result=True,
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-semantic-model")
    monkeypatch.setenv(
        "LIFEGUARD_PING_URL",
        "https://example.test/lifeguard",
    )

    provider_manager = Mock()
    provider_manager.build_named.return_value = {}
    monkeypatch.setattr(main, "ProviderManager", Mock(return_value=provider_manager))
    monkeypatch.setattr(
        main,
        "build_default_source_acquisition_policies",
        Mock(return_value={}),
    )

    source = Mock()
    source_factory = Mock(return_value=source)
    store = Mock()
    store_factory = Mock(return_value=store)
    service = Mock()
    service.restore.return_value = restore_result
    service.refresh.return_value = refresh_result
    service.portfolio = portfolio
    service.introduced_holdings = ()
    service_factory = Mock(return_value=service)
    runtime_factory_instance = Mock()
    runtime_factory = Mock(return_value=runtime_factory_instance)
    loop = Mock()
    loop_factory = Mock(return_value=loop)

    monkeypatch.setattr(
        main,
        "JsonFilePortfolioSource",
        source_factory,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "FilePortfolioTruthStore",
        store_factory,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "PortfolioTruthService",
        service_factory,
        raising=False,
    )
    monkeypatch.setattr(main, "SourceRuntimeFactory", runtime_factory)
    monkeypatch.setattr(main, "build_autonomous_loop", loop_factory)
    opening_store = Mock()
    opening_store.load.return_value = None
    monkeypatch.setattr(
        main,
        "FileSourceBootstrapStore",
        Mock(return_value=opening_store),
        raising=False,
    )

    return {
        "source_factory": source_factory,
        "store_factory": store_factory,
        "service": service,
        "service_factory": service_factory,
        "runtime_factory": runtime_factory,
        "loop": loop,
        "loop_factory": loop_factory,
    }


def test_main_uses_default_portfolio_paths(monkeypatch) -> None:
    monkeypatch.delenv("PORTFOLIO_SOURCE_PATH", raising=False)
    monkeypatch.delenv("PORTFOLIO_STATE_PATH", raising=False)
    context = _prepare_main(monkeypatch, portfolio=Portfolio([]))

    main.main()

    context["source_factory"].assert_called_once_with("portfolio_source.json")
    context["store_factory"].assert_called_once_with("portfolio_state.json")


def test_main_uses_configured_portfolio_paths(monkeypatch) -> None:
    monkeypatch.setenv("PORTFOLIO_SOURCE_PATH", "/data/portfolio_source.json")
    monkeypatch.setenv("PORTFOLIO_STATE_PATH", "/data/portfolio_state.json")
    context = _prepare_main(monkeypatch, portfolio=Portfolio([]))

    main.main()

    context["source_factory"].assert_called_once_with(
        "/data/portfolio_source.json"
    )
    context["store_factory"].assert_called_once_with(
        "/data/portfolio_state.json"
    )


def test_main_constructs_portfolio_truth_service_from_source_and_store(
    monkeypatch,
) -> None:
    context = _prepare_main(monkeypatch, portfolio=Portfolio([]))

    main.main()

    context["service_factory"].assert_called_once()
    args = context["service_factory"].call_args.args
    assert args[0] is context["source_factory"].return_value
    assert args[1] is context["store_factory"].return_value
    assert callable(args[2])
    assert args[2]().tzinfo is not None


def test_main_restores_then_refreshes_before_runtime_start(monkeypatch) -> None:
    calls = []
    context = _prepare_main(monkeypatch, portfolio=Portfolio([]))
    context["service"].restore.side_effect = lambda: calls.append("restore")
    context["service"].refresh.side_effect = lambda: calls.append("refresh")
    context["runtime_factory"].side_effect = lambda **_kwargs: (
        calls.append("runtime_factory") or Mock()
    )

    main.main()

    assert calls == ["restore", "refresh", "runtime_factory"]
    context["loop"].run.assert_called_once_with()


def test_restored_truth_starts_when_first_refresh_has_no_change(
    monkeypatch,
) -> None:
    restored = Portfolio([PortfolioHolding(symbol="AAPL", quantity=1)])
    context = _prepare_main(
        monkeypatch,
        portfolio=restored,
        restore_result=True,
        refresh_result=False,
    )

    main.main()

    kwargs = context["runtime_factory"].call_args.kwargs
    assert "portfolio_provider" in kwargs
    portfolio_provider = kwargs["portfolio_provider"]
    assert portfolio_provider() is restored
    context["loop"].run.assert_called_once_with()


def test_missing_truth_after_refresh_fails_before_loop(monkeypatch) -> None:
    context = _prepare_main(
        monkeypatch,
        portfolio=None,
        restore_result=False,
        refresh_result=False,
    )

    with pytest.raises(RuntimeError, match="Portfolio Truth"):
        main.main()

    context["runtime_factory"].assert_not_called()
    context["loop"].run.assert_not_called()


def test_missing_truth_then_complete_refresh_starts(monkeypatch) -> None:
    accepted = Portfolio([PortfolioHolding(symbol="MSFT", quantity=2)])
    context = _prepare_main(
        monkeypatch,
        portfolio=accepted,
        restore_result=False,
        refresh_result=True,
    )

    main.main()

    context["loop"].run.assert_called_once_with()


def test_authoritative_empty_portfolio_starts_without_watchlist_fallback(
    monkeypatch,
) -> None:
    empty = Portfolio([])
    context = _prepare_main(monkeypatch, portfolio=empty)

    main.main()

    kwargs = context["runtime_factory"].call_args.kwargs
    assert "portfolio_provider" in kwargs
    portfolio_provider = kwargs["portfolio_provider"]
    assert portfolio_provider() is empty
    assert portfolio_provider().holdings == []
    context["loop"].run.assert_called_once_with()


def test_malformed_state_stops_before_refresh_or_loop(monkeypatch) -> None:
    context = _prepare_main(monkeypatch, portfolio=None)
    context["service"].restore.side_effect = PortfolioTruthStorageError(
        "corrupt"
    )

    with pytest.raises(PortfolioTruthStorageError):
        main.main()

    context["service"].refresh.assert_not_called()
    context["runtime_factory"].assert_not_called()
    context["loop"].run.assert_not_called()


def test_runtime_factory_receives_dynamic_service_portfolio_provider(
    monkeypatch,
) -> None:
    first = Portfolio([PortfolioHolding(symbol="AAPL", quantity=1)])
    second = Portfolio([PortfolioHolding(symbol="MSFT", quantity=1)])
    context = _prepare_main(monkeypatch, portfolio=first)

    main.main()

    kwargs = context["runtime_factory"].call_args.kwargs
    assert "portfolio_provider" in kwargs
    provider = kwargs["portfolio_provider"]
    assert "watchlist" not in kwargs
    assert provider() is first

    context["service"].portfolio = second
    assert provider() is second


def test_main_has_no_static_watchlist_production_import(monkeypatch) -> None:
    context = _prepare_main(monkeypatch, portfolio=Portfolio([]))

    main.main()

    assert "WATCHLIST" not in vars(main)
    assert "watchlist" not in context["runtime_factory"].call_args.kwargs
