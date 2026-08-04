from unittest.mock import Mock

from engines.runtime_engine import RuntimeEngine
from models.event import Event
from modules.telegram_sender import TelegramSender


class FakePipeline:
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def collect_events(self, symbol: str) -> list[Event]:
        return self._events


def test_live_runtime_uses_injected_telegram_transport_without_real_network_call() -> None:
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

    telegram_api = Mock()
    telegram_sender_transport = TelegramSender(telegram_api=telegram_api)

    runtime = RuntimeEngine(
        watchlist=["LQDA"],
        pipeline=FakePipeline([event]),
        quote_fetcher=Mock(),
        telegram_sender=Mock(),
        live_preview_runner=Mock(),
        use_intelligence_notification_flow=True,
        telegram_sender_transport=telegram_sender_transport,
    )

    runtime.run()

    telegram_api.assert_called_once()
    assert "LQDA" in telegram_api.call_args.args[0]
    assert "SEC" in telegram_api.call_args.args[0]
