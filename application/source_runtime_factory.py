from collections.abc import Callable, Iterable

from application.investor_brief_enrichment_service import (
    InvestorBriefEnrichmentService,
)
from engines.intelligence_pipeline import IntelligencePipeline
from engines.runtime_engine import RuntimeEngine
from modules.notification_history import NotificationHistory
from modules.telegram_sender import TelegramSender


class SourceRuntimeFactory:
    def __init__(
        self,
        watchlist: Iterable[str],
        quote_fetcher: Callable[[str], dict],
        telegram_sender: Callable[[str], None],
        live_preview_runner: Callable[..., None],
        enrichment_service: InvestorBriefEnrichmentService,
        telegram_transport: TelegramSender,
        notification_history: NotificationHistory,
    ) -> None:
        self._watchlist = watchlist
        self._quote_fetcher = quote_fetcher
        self._telegram_sender = telegram_sender
        self._live_preview_runner = live_preview_runner
        self._enrichment_service = enrichment_service
        self._telegram_transport = telegram_transport
        self._notification_history = notification_history

    def __call__(
        self,
        pipeline: IntelligencePipeline,
    ) -> RuntimeEngine:
        return RuntimeEngine(
            watchlist=self._watchlist,
            pipeline=pipeline,
            quote_fetcher=self._quote_fetcher,
            telegram_sender=self._telegram_sender,
            live_preview_runner=self._live_preview_runner,
            investor_brief_enrichment_service=self._enrichment_service,
            use_intelligence_notification_flow=True,
            telegram_sender_transport=self._telegram_transport,
            notification_history=self._notification_history,
        )
