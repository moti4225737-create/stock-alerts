from unittest.mock import Mock

from application.source_runtime_factory import SourceRuntimeFactory
from engines.intelligence_pipeline import IntelligencePipeline
from engines.runtime_engine import RuntimeEngine


def test_source_runtime_factory_builds_existing_runtime_with_shared_dependencies() -> None:
    watchlist = ["LQDA"]
    quote_fetcher = Mock()
    telegram_sender = Mock()
    live_preview_runner = Mock()
    enrichment_service = Mock()
    telegram_transport = Mock()
    notification_history = Mock()

    factory = SourceRuntimeFactory(
        watchlist=watchlist,
        quote_fetcher=quote_fetcher,
        telegram_sender=telegram_sender,
        live_preview_runner=live_preview_runner,
        enrichment_service=enrichment_service,
        telegram_transport=telegram_transport,
        notification_history=notification_history,
    )

    pipeline = IntelligencePipeline(
        providers=[],
    )

    runtime = factory(pipeline)

    assert isinstance(runtime, RuntimeEngine)
    assert runtime._pipeline is pipeline
    assert runtime._watchlist is watchlist
    assert runtime._investor_brief_enrichment_service is enrichment_service
    assert runtime._telegram_sender_transport is telegram_transport
    assert runtime._notification_history is notification_history
    assert runtime._use_intelligence_notification_flow is True
