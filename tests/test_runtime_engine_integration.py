from unittest.mock import Mock

from engines.runtime_engine import RuntimeEngine
from models.event import Event
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding


class FakePipeline:
    def __init__(self, events_by_symbol: dict[str, list[Event]]) -> None:
        self._events_by_symbol = events_by_symbol

    def collect_events(self, symbol: str) -> list[Event]:
        return self._events_by_symbol.get(symbol, [])


def make_event(symbol: str, title: str) -> Event:
    return Event(
        symbol=symbol,
        source="SEC",
        title=title,
        summary=f"Summary for {symbol}",
        published_at="2026-08-03T10:00:00+00:00",
        importance=9,
        sentiment="neutral",
        url="https://www.sec.gov/example",
    )


def test_runtime_with_no_intelligence_messages_sends_nothing() -> None:
    telegram_sender = Mock()
    pipeline = FakePipeline({})

    runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=pipeline,
        telegram_sender=telegram_sender,
    )

    runtime.run()

    telegram_sender.assert_not_called()


def test_runtime_with_one_brief_sends_one_telegram_message() -> None:
    telegram_sender = Mock()
    pipeline = FakePipeline({"LQDA": [make_event("LQDA", "SEC Filing")]})

    runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=pipeline,
        telegram_sender=telegram_sender,
    )

    runtime.run()

    assert telegram_sender.call_count == 1
    assert "LQDA" in telegram_sender.call_args.args[0]
    assert "SEC" in telegram_sender.call_args.args[0]


def test_runtime_with_multiple_briefs_delivers_in_order() -> None:
    telegram_sender = Mock()
    pipeline = FakePipeline(
        {
            "AAPL": [make_event("AAPL", "First")],
            "MSFT": [make_event("MSFT", "Second")],
        }
    )

    runtime = RuntimeEngine(
        portfolio=Portfolio(
            [
                PortfolioHolding(symbol="AAPL", quantity=1),
                PortfolioHolding(symbol="MSFT", quantity=1),
            ]
        ),
        pipeline=pipeline,
        telegram_sender=telegram_sender,
    )

    runtime.run()

    assert telegram_sender.call_count == 2
    assert "AAPL" in telegram_sender.call_args_list[0].args[0]
    assert "MSFT" in telegram_sender.call_args_list[1].args[0]
