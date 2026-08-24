from collections.abc import Callable

from application.investor_brief_enrichment_service import (
    InvestorBriefEnrichmentService,
)
from engines.intelligence_pipeline import IntelligencePipeline
from engines.runtime_engine import RuntimeEngine
from models.portfolio import Portfolio
from modules.notification_history import NotificationHistory
from modules.telegram_sender import TelegramSender


class SourceRuntimeFactory:
    def __init__(
        self,
        portfolio_provider: Callable[[], Portfolio | None],
        telegram_sender: Callable[[str], None],
        enrichment_service: InvestorBriefEnrichmentService,
        telegram_transport: TelegramSender,
        notification_history: NotificationHistory,
    ) -> None:
        self._portfolio_provider = portfolio_provider
        self._telegram_sender = telegram_sender
        self._enrichment_service = enrichment_service
        self._telegram_transport = telegram_transport
        self._notification_history = notification_history

    def __call__(
        self,
        pipeline: IntelligencePipeline,
    ) -> RuntimeEngine:
        portfolio = self._portfolio_provider()
        if portfolio is None:
            raise RuntimeError("Portfolio Truth is unavailable")

        return RuntimeEngine(
            portfolio=portfolio,
            pipeline=pipeline,
            telegram_sender=self._telegram_sender,
            investor_brief_enrichment_service=self._enrichment_service,
            telegram_sender_transport=self._telegram_transport,
            notification_history=self._notification_history,
        )
