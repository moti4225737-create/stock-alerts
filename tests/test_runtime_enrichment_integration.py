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


def make_brief(title: str) -> InvestorBrief:
    event = Event(
        symbol="LQDA",
        source="SEC",
        title=title,
        summary="Basic summary",
        published_at="2026-08-06T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
        url=f"https://www.sec.gov/{title}",
    )
    holding = PortfolioHolding(
        symbol="LQDA",
        quantity=1,
        average_cost=0,
    )

    return InvestorBrief(
        event=event,
        ranking_position=1,
        portfolio_impact=PortfolioImpact(
            holding=holding,
            event=event,
            matches_portfolio=True,
        ),
        headline=event.title,
        summary=event.summary,
        explanation=Explanation(
            why_it_matters="Basic explanation",
            market_context="Basic context",
        ),
    )


class FakePortfolioIntelligenceService:
    def __init__(self, briefs: list[InvestorBrief]) -> None:
        self._briefs = briefs

    def build_briefs(
        self,
        portfolio: object,
        provider: object,
    ) -> tuple[list[InvestorBrief], list[str]]:
        return self._briefs, []


class RecordingEnrichmentService:
    def __init__(
        self,
        enriched: InvestorBrief,
    ) -> None:
        self.enriched = enriched
        self.received: list[InvestorBrief] | None = None

    def enrich_all(
        self,
        briefs: list[InvestorBrief],
    ) -> tuple[InvestorBrief, ...]:
        self.received = list(briefs)
        return (self.enriched,)


class RecordingNotificationService:
    def __init__(self) -> None:
        self.received: list[InvestorBrief] | None = None

    def generate_messages(
        self,
        briefs: list[InvestorBrief],
    ) -> tuple[str, ...]:
        self.received = list(briefs)
        return ("enriched message",)


def test_runtime_enriches_only_pending_briefs_before_delivery(
    tmp_path: Path,
) -> None:
    delivered = make_brief("Already delivered")
    pending = make_brief("New filing")
    enriched_pending = make_brief("Enriched filing")

    history = NotificationHistory(tmp_path / "history.txt")
    delivered_id = (
        f"{delivered.event.source}|"
        f"{delivered.event.symbol}|"
        f"{delivered.event.title}|"
        f"{delivered.event.published_at}|"
        f"{delivered.event.url}"
    )
    history.record(delivered_id)

    enrichment_service = RecordingEnrichmentService(
        enriched_pending,
    )
    notification_service = RecordingNotificationService()
    telegram_sender = Mock()

    runtime = RuntimeEngine(
        portfolio=Portfolio([PortfolioHolding(symbol="LQDA", quantity=1)]),
        pipeline=Mock(),
        telegram_sender=telegram_sender,
        portfolio_intelligence_service=(
            FakePortfolioIntelligenceService(
                [delivered, pending]
            )
        ),
        investor_notification_service=notification_service,
        investor_brief_enrichment_service=enrichment_service,
        notification_history=history,
    )

    runtime.run()

    assert enrichment_service.received == [pending]
    assert notification_service.received == [enriched_pending]
    telegram_sender.assert_called_once_with(
        "enriched message"
    )
