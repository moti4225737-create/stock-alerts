from collections.abc import Callable, Iterable
from typing import Any

from application.investor_notification_service import InvestorNotificationService
from engines.intelligence_pipeline import IntelligencePipeline
from engines.portfolio_intelligence_service import PortfolioIntelligenceService
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from modules.telegram_sender import TelegramSender


class _PipelineProvider:
    def __init__(self, pipeline: IntelligencePipeline) -> None:
        self._pipeline = pipeline

    def fetch_events(self, symbol: str) -> list:
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
        watchlist: Iterable[str],
        pipeline: IntelligencePipeline,
        quote_fetcher: Callable[[str], dict[str, Any]],
        telegram_sender: Callable[[str], None],
        live_preview_runner: Callable[..., None],
        portfolio_intelligence_service: PortfolioIntelligenceService | None = None,
        investor_notification_service: InvestorNotificationService | None = None,
        telegram_sender_transport: TelegramSender | None = None,
        use_intelligence_notification_flow: bool = False,
    ) -> None:
        self._watchlist = watchlist
        self._pipeline = pipeline
        self._quote_fetcher = quote_fetcher
        self._telegram_sender = telegram_sender
        self._live_preview_runner = live_preview_runner
        self._portfolio_intelligence_service = (
            portfolio_intelligence_service or PortfolioIntelligenceService()
        )
        self._investor_notification_service = (
            investor_notification_service or InvestorNotificationService()
        )
        self._telegram_sender_transport = telegram_sender_transport or TelegramSender(
            telegram_api=telegram_sender,
        )
        self._use_intelligence_notification_flow = use_intelligence_notification_flow

    def run(self) -> None:
        """
        Execute one complete Stock Sentinel runtime cycle.
        """
        if self._use_intelligence_notification_flow:
            holdings = [
                PortfolioHolding(symbol=str(symbol).strip().upper(), quantity=1, average_cost=0)
                for symbol in self._watchlist
                if str(symbol).strip()
            ]
            portfolio = Portfolio(holdings)
            provider = _PipelineProvider(self._pipeline)
            briefs, _ = self._portfolio_intelligence_service.build_briefs(
                portfolio,
                provider,
            )
            messages = self._investor_notification_service.generate_messages(briefs)
            self._telegram_sender_transport.send_messages(messages)
            return

        self._live_preview_runner(
            watchlist=self._watchlist,
            pipeline=self._pipeline,
            quote_fetcher=self._quote_fetcher,
            telegram_sender=self._telegram_sender,
        )