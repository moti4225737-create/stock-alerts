from unittest.mock import Mock

from engines.runtime_engine import RuntimeEngine
from models.event import Event


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
        watchlist=["LQDA"],
        pipeline=pipeline,
        quote_fetcher=Mock(),
        telegram_sender=telegram_sender,
        live_preview_runner=Mock(),
        use_intelligence_notification_flow=True,
    )

    runtime.run()

    telegram_sender.assert_not_called()


def test_runtime_with_one_brief_sends_one_telegram_message() -> None:
    telegram_sender = Mock()
    pipeline = FakePipeline({"LQDA": [make_event("LQDA", "SEC Filing")]})

    runtime = RuntimeEngine(
        watchlist=["LQDA"],
        pipeline=pipeline,
        quote_fetcher=Mock(),
        telegram_sender=telegram_sender,
        live_preview_runner=Mock(),
        use_intelligence_notification_flow=True,
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
        watchlist=["AAPL", "MSFT"],
        pipeline=pipeline,
        quote_fetcher=Mock(),
        telegram_sender=telegram_sender,
        live_preview_runner=Mock(),
        use_intelligence_notification_flow=True,
    )

    runtime.run()

    assert telegram_sender.call_count == 2
    assert "AAPL" in telegram_sender.call_args_list[0].args[0]
    assert "MSFT" in telegram_sender.call_args_list[1].args[0]


def test_runtime_engine_delegates_to_existing_send_telegram_callable() -> None:
    telegram_sender = Mock()
    live_preview_runner = Mock()

    runtime = RuntimeEngine(
        watchlist=["LQDA"],
        pipeline=Mock(),
        quote_fetcher=Mock(),
        telegram_sender=telegram_sender,
        live_preview_runner=live_preview_runner,
    )

    runtime.run()

    live_preview_runner.assert_called_once_with(
        watchlist=["LQDA"],
        pipeline=runtime._pipeline,
        quote_fetcher=runtime._quote_fetcher,
        telegram_sender=telegram_sender,
    )
