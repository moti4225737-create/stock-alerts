from collections.abc import Callable
from pathlib import Path

from application.investor_brief_enrichment_service import (
    InvestorBriefEnrichmentService,
)
from application.investor_notification_service import (
    InvestorNotificationService,
)
from engines.intelligence_pipeline import IntelligencePipeline
from engines.portfolio_intelligence_service import (
    PortfolioIntelligenceService,
)
from models.investor_brief import InvestorBrief
from models.portfolio import Portfolio
from modules.notification_history import NotificationHistory
from modules.telegram_sender import TelegramSender


class _PipelineProvider:
    def __init__(
        self,
        pipeline: IntelligencePipeline,
    ) -> None:
        self._pipeline = pipeline

    def fetch_events(
        self,
        symbol: str,
    ) -> list:
        return self._pipeline.collect_events(symbol)


class RuntimeEngine:
    """
    Coordinate one runtime execution of Stock Sentinel.

    The engine receives all external dependencies through its constructor,
    keeping runtime orchestration independent from concrete providers,
    Telegram, and quote services.
    """

    def __init__(
        self,
        portfolio: Portfolio,
        pipeline: IntelligencePipeline,
        telegram_sender: Callable[[str], None],
        portfolio_intelligence_service: (
            PortfolioIntelligenceService | None
        ) = None,
        investor_notification_service: (
            InvestorNotificationService | None
        ) = None,
        investor_brief_enrichment_service: (
            InvestorBriefEnrichmentService | None
        ) = None,
        telegram_sender_transport: TelegramSender | None = None,
        history_path: Path | None = None,
        notification_history: NotificationHistory | None = None,
    ) -> None:
        self._portfolio = portfolio
        self._pipeline = pipeline
        self._telegram_sender = telegram_sender
        self._portfolio_intelligence_service = (
            portfolio_intelligence_service
            or PortfolioIntelligenceService()
        )
        self._investor_notification_service = (
            investor_notification_service
            or InvestorNotificationService()
        )
        self._investor_brief_enrichment_service = (
            investor_brief_enrichment_service
            or InvestorBriefEnrichmentService(enrichers=())
        )
        self._telegram_sender_transport = (
            telegram_sender_transport
            or TelegramSender(
                telegram_api=telegram_sender,
            )
        )
        self._history_path = history_path
        self._notification_history = (
            notification_history
            or NotificationHistory(self._history_path)
        )

    def _get_event_id(
        self,
        brief: object,
    ) -> str:
        event = getattr(brief, "event", None)

        if event is None:
            return ""

        source = getattr(event, "source", "") or ""
        symbol = getattr(event, "symbol", "") or ""
        title = getattr(event, "title", "") or ""
        published_at = getattr(event, "published_at", "") or ""
        url = getattr(event, "url", "") or ""

        return (
            f"{source}|{symbol}|{title}|"
            f"{published_at}|{url}"
        )

    def run(self) -> None:
        """
        Execute one complete Stock Sentinel runtime cycle.
        """
        provider = _PipelineProvider(self._pipeline)

        briefs, _ = (
            self._portfolio_intelligence_service.build_briefs(
                self._portfolio,
                provider,
            )
        )

        pending_briefs: list[InvestorBrief] = []
        pending_event_ids: list[str] = []
        seen_event_ids: set[str] = set()

        for brief in briefs:
            event_id = self._get_event_id(brief)

            if self._notification_history.has_delivered(
                event_id
            ):
                continue

            if event_id and event_id in seen_event_ids:
                continue

            pending_briefs.append(brief)
            pending_event_ids.append(event_id)

            if event_id:
                seen_event_ids.add(event_id)

        if pending_briefs:
            enriched_briefs = list(
                self._investor_brief_enrichment_service.enrich_all(
                    pending_briefs
                )
            )
            messages = (
                self._investor_notification_service.generate_messages(
                    enriched_briefs
                )
            )
            self._telegram_sender_transport.send_messages(
                messages
            )

            for event_id in pending_event_ids:
                if event_id:
                    self._notification_history.record(
                        event_id
                    )
