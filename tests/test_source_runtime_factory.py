from unittest.mock import Mock

import pytest

import application.source_runtime_factory as factory_module
from application.source_runtime_factory import SourceRuntimeFactory
from engines.intelligence_pipeline import IntelligencePipeline
from engines.runtime_engine import RuntimeEngine
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding


def _portfolio(symbol: str) -> Portfolio:
    return Portfolio([PortfolioHolding(symbol=symbol, quantity=1)])


def _factory(portfolio_provider) -> SourceRuntimeFactory:
    return SourceRuntimeFactory(
        portfolio_provider=portfolio_provider,
        telegram_sender=Mock(),
        enrichment_service=Mock(),
        telegram_transport=Mock(),
        notification_history=Mock(),
    )


def test_source_runtime_factory_passes_current_portfolio_to_runtime() -> None:
    portfolio = _portfolio("LQDA")
    provider = Mock(return_value=portfolio)
    factory = _factory(provider)
    pipeline = IntelligencePipeline(providers=[])

    runtime = factory(pipeline)

    assert isinstance(runtime, RuntimeEngine)
    assert runtime._pipeline is pipeline
    assert runtime._portfolio is portfolio
    provider.assert_called_once_with()


def test_factory_resolves_portfolio_for_each_new_runtime() -> None:
    first = _portfolio("AAPL")
    second = _portfolio("MSFT")
    provider = Mock(side_effect=[first, second])
    factory = _factory(provider)
    pipeline = IntelligencePipeline(providers=[])

    first_runtime = factory(pipeline)
    second_runtime = factory(pipeline)

    assert first_runtime._portfolio is first
    assert second_runtime._portfolio is second
    assert provider.call_count == 2


def test_factory_accepts_authoritative_empty_portfolio() -> None:
    empty = Portfolio([])
    factory = _factory(Mock(return_value=empty))

    runtime = factory(IntelligencePipeline(providers=[]))

    assert runtime._portfolio is empty


def test_factory_rejects_absent_truth_before_runtime_creation(
    monkeypatch,
) -> None:
    runtime_factory = Mock()
    monkeypatch.setattr(factory_module, "RuntimeEngine", runtime_factory)
    factory = _factory(Mock(return_value=None))

    with pytest.raises(RuntimeError, match="Portfolio Truth"):
        factory(IntelligencePipeline(providers=[]))

    runtime_factory.assert_not_called()


def test_factory_has_no_production_watchlist_state() -> None:
    factory = _factory(Mock(return_value=Portfolio([])))

    assert not hasattr(factory, "_watchlist")
