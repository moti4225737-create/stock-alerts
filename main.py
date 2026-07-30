import os
from collections.abc import Callable, Iterable

import requests
from dotenv import load_dotenv

from alerts import Alert, format_alert
from engines.intelligence_pipeline import IntelligencePipeline
from engines.runtime_engine import RuntimeEngine
from models.event import Event
from modules.finnhub_client import get_quote
from modules.provider_manager import ProviderManager
from modules.ticker_resolver import TickerResolver
from watchlist import WATCHLIST


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
    Run the live preview for every symbol in the watchlist.

    For each symbol:
    - fetch the latest Finnhub quote
    - collect provider intelligence events
    - send all valid results to Telegram
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


def main() -> None:
    """
    Configure Stock Sentinel and execute one runtime cycle.
    """
    ticker_resolver = TickerResolver()

    provider_manager = ProviderManager(
        ticker_resolver=ticker_resolver,
    )

    pipeline = IntelligencePipeline(
        providers=provider_manager.build(),
    )

    runtime = RuntimeEngine(
        watchlist=WATCHLIST,
        pipeline=pipeline,
        quote_fetcher=get_quote,
        telegram_sender=send_telegram,
        live_preview_runner=run_live_preview,
    )

    runtime.run()


if __name__ == "__main__":
    main()