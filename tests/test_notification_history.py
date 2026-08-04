from pathlib import Path
from unittest.mock import Mock

from engines.runtime_engine import RuntimeEngine
from models.event import Event
from modules.notification_history import NotificationHistory


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


def test_first_runtime_instance_sends_new_event_and_second_instance_skips_it(tmp_path: Path) -> None:
    history_path = tmp_path / "history.txt"
    history = NotificationHistory(history_path)
    first_runtime = RuntimeEngine(
        watchlist=["LQDA"],
        pipeline=FakePipeline({"LQDA": [make_event("LQDA", "First")]}),
        quote_fetcher=Mock(),
        telegram_sender=Mock(),
        live_preview_runner=Mock(),
        use_intelligence_notification_flow=True,
        notification_history=history,
    )

    first_runtime.run()

    second_runtime = RuntimeEngine(
        watchlist=["LQDA"],
        pipeline=FakePipeline({"LQDA": [make_event("LQDA", "First")]}),
        quote_fetcher=Mock(),
        telegram_sender=Mock(),
        live_preview_runner=Mock(),
        use_intelligence_notification_flow=True,
        notification_history=NotificationHistory(history_path),
    )

    second_runtime.run()

    assert first_runtime._telegram_sender_transport._telegram_api.call_count == 1
    assert second_runtime._telegram_sender_transport._telegram_api.call_count == 0


def test_later_new_event_is_the_only_event_sent(tmp_path: Path) -> None:
    history_path = tmp_path / "history.txt"
    history = NotificationHistory(history_path)
    first_runtime = RuntimeEngine(
        watchlist=["LQDA"],
        pipeline=FakePipeline({"LQDA": [make_event("LQDA", "First")]}),
        quote_fetcher=Mock(),
        telegram_sender=Mock(),
        live_preview_runner=Mock(),
        use_intelligence_notification_flow=True,
        notification_history=history,
    )

    first_runtime.run()

    second_runtime = RuntimeEngine(
        watchlist=["LQDA"],
        pipeline=FakePipeline({"LQDA": [make_event("LQDA", "First"), make_event("LQDA", "Second")]}),
        quote_fetcher=Mock(),
        telegram_sender=Mock(),
        live_preview_runner=Mock(),
        use_intelligence_notification_flow=True,
        notification_history=NotificationHistory(history_path),
    )

    second_runtime.run()

    assert first_runtime._telegram_sender_transport._telegram_api.call_count == 1
    assert second_runtime._telegram_sender_transport._telegram_api.call_count == 1
