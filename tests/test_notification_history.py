from pathlib import Path
from unittest.mock import Mock

from engines.runtime_engine import RuntimeEngine
from models.event import Event
from models.explanation import Explanation
from models.investor_brief import InvestorBrief
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from models.portfolio_impact import PortfolioImpact
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


def make_brief(event: Event) -> InvestorBrief:
    impact = PortfolioImpact(
        holding=PortfolioHolding(symbol=event.symbol, quantity=1, average_cost=0),
        event=event,
        matches_portfolio=True,
    )
    explanation = Explanation(why_it_matters="why it matters", market_context="market context")
    return InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=impact,
        headline=event.title,
        summary=event.summary,
        explanation=explanation,
    )


class FakePortfolioIntelligenceService:
    def __init__(self, briefs: list[InvestorBrief]) -> None:
        self._briefs = briefs
        self.calls: list[tuple[object, object]] = []

    def build_briefs(self, portfolio: object, provider: object) -> tuple[list[InvestorBrief], list[str]]:
        self.calls.append((portfolio, provider))
        return self._briefs, []


class FakeInvestorNotificationService:
    def __init__(self) -> None:
        self.calls: list[list[InvestorBrief]] = []

    def generate_messages(self, briefs: list[InvestorBrief]) -> tuple[str, ...]:
        self.calls.append(list(briefs))
        return tuple(f"message:{brief.event.title}" for brief in briefs)


def test_duplicate_briefs_in_same_run_only_send_once(tmp_path: Path) -> None:
    history_path = tmp_path / "history.txt"
    history = NotificationHistory(history_path)
    duplicate_brief = make_brief(make_event("LQDA", "First"))
    notification_service = FakeInvestorNotificationService()
    telegram_sender = Mock()

    runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=FakePipeline({"LQDA": []}),
        telegram_sender=telegram_sender,
        portfolio_intelligence_service=FakePortfolioIntelligenceService([duplicate_brief, duplicate_brief]),
        investor_notification_service=notification_service,
        notification_history=history,
    )

    runtime.run()

    assert telegram_sender.call_count == 1
    assert len(notification_service.calls[0]) == 1


def test_distinct_briefs_in_same_run_preserve_order_and_send_twice(tmp_path: Path) -> None:
    history_path = tmp_path / "history.txt"
    history = NotificationHistory(history_path)
    notification_service = FakeInvestorNotificationService()
    telegram_sender = Mock()

    first_brief = make_brief(make_event("LQDA", "First"))
    second_brief = make_brief(make_event("LQDA", "Second"))

    runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=FakePipeline({"LQDA": []}),
        telegram_sender=telegram_sender,
        portfolio_intelligence_service=FakePortfolioIntelligenceService([first_brief, second_brief]),
        investor_notification_service=notification_service,
        notification_history=history,
    )

    runtime.run()

    assert telegram_sender.call_count == 2
    assert [brief.event.title for brief in notification_service.calls[0]] == ["First", "Second"]


def test_first_runtime_instance_sends_new_event_and_second_instance_skips_it(tmp_path: Path) -> None:
    history_path = tmp_path / "history.txt"
    history = NotificationHistory(history_path)
    first_runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=FakePipeline({"LQDA": [make_event("LQDA", "First")]}),
        telegram_sender=Mock(),
        notification_history=history,
    )

    first_runtime.run()

    second_runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=FakePipeline({"LQDA": [make_event("LQDA", "First")]}),
        telegram_sender=Mock(),
        notification_history=NotificationHistory(history_path),
    )

    second_runtime.run()

    assert first_runtime._telegram_sender_transport._telegram_api.call_count == 1
    assert second_runtime._telegram_sender_transport._telegram_api.call_count == 0


def test_later_new_event_is_the_only_event_sent(tmp_path: Path) -> None:
    history_path = tmp_path / "history.txt"
    history = NotificationHistory(history_path)
    first_runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=FakePipeline({"LQDA": [make_event("LQDA", "First")]}),
        telegram_sender=Mock(),
        notification_history=history,
    )

    first_runtime.run()

    second_runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=FakePipeline({"LQDA": [make_event("LQDA", "First"), make_event("LQDA", "Second")]}),
        telegram_sender=Mock(),
        notification_history=NotificationHistory(history_path),
    )

    second_runtime.run()

    assert first_runtime._telegram_sender_transport._telegram_api.call_count == 1
    assert second_runtime._telegram_sender_transport._telegram_api.call_count == 1
