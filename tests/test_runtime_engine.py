from unittest.mock import Mock

from engines.runtime_engine import RuntimeEngine


def test_runtime_engine_runs_live_preview_with_configured_dependencies():
    watchlist = ["LQDA", "AAPL"]
    pipeline = Mock()
    quote_fetcher = Mock()
    telegram_sender = Mock()
    live_preview_runner = Mock()

    runtime = RuntimeEngine(
        watchlist=watchlist,
        pipeline=pipeline,
        quote_fetcher=quote_fetcher,
        telegram_sender=telegram_sender,
        live_preview_runner=live_preview_runner,
    )

    runtime.run()

    live_preview_runner.assert_called_once_with(
        watchlist=watchlist,
        pipeline=pipeline,
        quote_fetcher=quote_fetcher,
        telegram_sender=telegram_sender,
    )