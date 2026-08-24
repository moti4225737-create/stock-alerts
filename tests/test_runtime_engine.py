from decimal import Decimal
from unittest.mock import Mock

from engines.runtime_engine import RuntimeEngine
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding


def test_runtime_engine_uses_real_portfolio_without_synthetic_replacement():
    holding = PortfolioHolding(
        symbol="LQDA",
        quantity=Decimal("7.99"),
        average_cost=66.79,
    )
    portfolio = Portfolio([holding])
    pipeline = Mock()
    telegram_sender = Mock()
    intelligence_service = Mock()
    intelligence_service.build_briefs.return_value = ([], [])

    runtime = RuntimeEngine(
        portfolio=portfolio,
        pipeline=pipeline,
        telegram_sender=telegram_sender,
        portfolio_intelligence_service=intelligence_service,
    )

    runtime.run()

    received_portfolio = intelligence_service.build_briefs.call_args.args[0]
    received_holding = received_portfolio.holdings[0]
    assert received_holding.symbol == "LQDA"
    assert received_holding.quantity == Decimal("7.99")
    assert received_holding.average_cost == 66.79


def test_authoritative_empty_portfolio_performs_no_portfolio_aware_work():
    portfolio = Portfolio([])
    pipeline = Mock()
    telegram_sender = Mock()

    runtime = RuntimeEngine(
        portfolio=portfolio,
        pipeline=pipeline,
        telegram_sender=telegram_sender,
    )

    runtime.run()

    pipeline.collect_events.assert_not_called()
    telegram_sender.assert_not_called()
