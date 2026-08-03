from unittest.mock import Mock

import main
from engines.runtime_engine import RuntimeEngine
from models.event import Event
from modules.telegram_sender import TelegramSender


class FakePipeline:
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def collect_events(self, symbol: str) -> list[Event]:
        return self._events


def test_main_runtime_uses_existing_send_telegram_via_runtime_engine() -> None:
    event = Event(
        symbol="LQDA",
        source="SEC",
        title="SEC Filing",
        summary="Material filing.",
        published_at="2026-08-03T10:00:00+00:00",
        importance=9,
        sentiment="neutral",
        url="https://www.sec.gov/example",
    )

    runtime = RuntimeEngine(
        watchlist=["LQDA"],
        pipeline=FakePipeline([event]),
        quote_fetcher=Mock(),
        telegram_sender=main.send_telegram,
        live_preview_runner=main.run_live_preview,
        use_intelligence_notification_flow=True,
    )

    telegram_sender_transport = TelegramSender(telegram_api=main.send_telegram)
    runtime._telegram_sender_transport = telegram_sender_transport

    runtime.run()

    assert runtime._telegram_sender_transport._telegram_api is main.send_telegram
