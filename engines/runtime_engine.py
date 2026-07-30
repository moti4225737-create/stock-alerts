from collections.abc import Callable, Iterable
from typing import Any

from engines.intelligence_pipeline import IntelligencePipeline


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
    ) -> None:
        self._watchlist = watchlist
        self._pipeline = pipeline
        self._quote_fetcher = quote_fetcher
        self._telegram_sender = telegram_sender
        self._live_preview_runner = live_preview_runner

    def run(self) -> None:
        """
        Execute one complete Stock Sentinel runtime cycle.
        """
        self._live_preview_runner(
            watchlist=self._watchlist,
            pipeline=self._pipeline,
            quote_fetcher=self._quote_fetcher,
            telegram_sender=self._telegram_sender,
        )