import os
import time
from collections.abc import Callable, Iterable
from datetime import datetime, time as clock_time, timezone

import requests
from dotenv import load_dotenv
from openai import OpenAI

from alerts import Alert, format_alert
from application.autonomous_acquisition_loop import (
    AutonomousAcquisitionLoop,
)
from application.autonomous_source_acquisition import (
    build_autonomous_source_acquisition,
)
from application.default_investor_brief_enrichment import (
    build_default_investor_brief_enrichment_service,
)
from application.portfolio_truth_service import PortfolioTruthService
from application.source_runtime_factory import SourceRuntimeFactory
from engines.intelligence_pipeline import IntelligencePipeline
from engines.source_acquisition_policy import SourceAcquisitionPolicy
from models.event import Event
from modules.file_portfolio_truth_store import FilePortfolioTruthStore
from modules.healthchecks_work_evidence_reporter import (
    HealthchecksWorkEvidenceReporter,
)
from modules.json_file_portfolio_source import JsonFilePortfolioSource
from modules.notification_history import NotificationHistory
from modules.provider_manager import ProviderManager
from modules.telegram_sender import TelegramSender
from modules.ticker_resolver import TickerResolver
from product.openai_semantic_finding_analyzer import (
    OpenAISemanticFindingAnalyzer,
)
from product.semantic_finding_analyzer_adapter import (
    SemanticFindingAnalyzerAdapter,
)
from product.openai_semantic_significance_assessor import (
    OpenAISemanticSignificanceAssessor,
)


load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(message: str) -> None:
    """
    Send one formatted message to the configured Telegram chat.
    """
    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        },
        timeout=20,
    ).raise_for_status()


def _importance_to_severity(importance: int) -> str:
    """
    Convert an event importance score into an alert severity label.
    """
    if importance >= 8:
        return "CRITICAL"

    if importance >= 5:
        return "HIGH"

    if importance >= 3:
        return "MEDIUM"

    return "INFO"


def _format_event_message(event: Event) -> str:
    """
    Build the detailed body shown for an intelligence event.
    """
    message_parts = [
        event.summary,
        f"Published: {event.published_at or 'Unknown'}",
        f"Sentiment: {event.sentiment}",
        f"Importance: {event.importance}/10",
    ]

    if event.url:
        message_parts.append(f"URL: {event.url}")

    return "\n".join(message_parts)


def _event_to_alert(event: Event) -> Alert:
    """
    Convert a normalized intelligence Event into a Telegram Alert.
    """
    return Alert(
        source=event.source,
        symbol=event.symbol,
        title=event.title,
        severity=_importance_to_severity(event.importance),
        message=_format_event_message(event),
    )


def run_live_preview(
    watchlist: Iterable[str],
    pipeline: IntelligencePipeline,
    quote_fetcher: Callable[[str], dict],
    telegram_sender: Callable[[str], None],
) -> None:
    """
    Run the legacy live preview for every symbol in the watchlist.
    """
    for symbol in watchlist:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            continue

        try:
            quote = quote_fetcher(normalized_symbol)
            price = quote.get("c")

            if price not in (None, 0):
                quote_alert = Alert(
                    source="Finnhub",
                    symbol=normalized_symbol,
                    title="Price Update",
                    severity="INFO",
                    message=f"Current Price: ${price}",
                )

                telegram_sender(format_alert(quote_alert))

        except (
            requests.RequestException,
            RuntimeError,
            ValueError,
            OSError,
        ) as error:
            print(
                f"[WARNING] Finnhub quote failed for "
                f"{normalized_symbol}: {error}"
            )

        events = pipeline.collect_events(normalized_symbol)

        for event in events:
            telegram_sender(
                format_alert(
                    _event_to_alert(event)
                )
            )


def build_default_source_acquisition_policies(
) -> dict[str, SourceAcquisitionPolicy]:
    """
    Build the approved v0.5 acquisition policies.
    """
    return {
        "FDA": SourceAcquisitionPolicy(
            source_name="FDA",
            interval_seconds=3600,
        ),
        "ClinicalTrials.gov": SourceAcquisitionPolicy(
            source_name="ClinicalTrials.gov",
            interval_seconds=3600,
            publication_time=clock_time(hour=9),
            publication_window_minutes=15,
            publication_interval_seconds=60,
            publication_timezone="America/New_York",
        ),
        "SEC": SourceAcquisitionPolicy(
            source_name="SEC",
            interval_seconds=60,
        ),
    }


def build_autonomous_loop(
    providers: dict,
    policies: dict[str, SourceAcquisitionPolicy],
    runtime_factory: SourceRuntimeFactory,
    work_evidence_reporter: Callable[..., None] | None = None,
) -> AutonomousAcquisitionLoop:
    """
    Build the autonomous source-acquisition execution loop.
    """
    coordinator = build_autonomous_source_acquisition(
        providers=providers,
        policies=policies,
        runtime_factory=runtime_factory,
        work_evidence_reporter=work_evidence_reporter,
    )

    return AutonomousAcquisitionLoop(
        coordinator=coordinator,
        clock=lambda: datetime.now(timezone.utc),
        waiter=time.sleep,
        tick_seconds=1,
    )


def main() -> None:
    """
    Configure Stock Sentinel and run autonomous source acquisition.
    """
    ticker_resolver = TickerResolver()

    provider_manager = ProviderManager(
        ticker_resolver=ticker_resolver,
    )

    providers = provider_manager.build_named()
    policies = build_default_source_acquisition_policies()

    notification_history_path = os.environ.get(
        "NOTIFICATION_HISTORY_PATH",
        "notification_history.txt",
    )

    notification_history = NotificationHistory(
        notification_history_path
    )

    telegram_transport = TelegramSender(
        telegram_api=send_telegram,
    )

    openai_client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
    )

    semantic_execution_analyzer = OpenAISemanticFindingAnalyzer(
        client=openai_client,
        model=os.environ["OPENAI_MODEL"],
    )

    semantic_analyzer = SemanticFindingAnalyzerAdapter(
        execution_analyzer=semantic_execution_analyzer,
    )

    significance_assessor = OpenAISemanticSignificanceAssessor(
        client=openai_client,
        model=os.environ["OPENAI_MODEL"],
    )

    enrichment_service = (
        build_default_investor_brief_enrichment_service(
            user_agent=os.environ["SEC_USER_AGENT"],
            semantic_analyzer=semantic_analyzer,
            significance_assessor=significance_assessor,
        )
    )

    portfolio_source = JsonFilePortfolioSource(
        os.environ.get(
            "PORTFOLIO_SOURCE_PATH",
            "portfolio_source.json",
        )
    )
    portfolio_store = FilePortfolioTruthStore(
        os.environ.get(
            "PORTFOLIO_STATE_PATH",
            "portfolio_state.json",
        )
    )
    portfolio_service = PortfolioTruthService(
        portfolio_source,
        portfolio_store,
        lambda: datetime.now(timezone.utc),
    )
    portfolio_service.restore()
    portfolio_service.refresh()

    if portfolio_service.portfolio is None:
        raise RuntimeError("Portfolio Truth is unavailable")

    runtime_factory = SourceRuntimeFactory(
        portfolio_provider=lambda: portfolio_service.portfolio,
        telegram_sender=send_telegram,
        enrichment_service=enrichment_service,
        telegram_transport=telegram_transport,
        notification_history=notification_history,
    )

    work_evidence_reporter = HealthchecksWorkEvidenceReporter(
        ping_url=os.environ["LIFEGUARD_PING_URL"],
        requester=requests.get,
    )

    autonomous_loop = build_autonomous_loop(
        providers=providers,
        policies=policies,
        runtime_factory=runtime_factory,
        work_evidence_reporter=work_evidence_reporter,
    )

    autonomous_loop.run()


if __name__ == "__main__":
    main()
