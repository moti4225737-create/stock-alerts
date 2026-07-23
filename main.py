import os
import requests

from dotenv import load_dotenv

from watchlist import WATCHLIST
from alerts import Alert, format_alert
from modules.finnhub_client import get_quote

# Load environment variables from .env
load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        },
        timeout=20,
    ).raise_for_status()


def main():
    for symbol in WATCHLIST:
        quote = get_quote(symbol)

        price = quote.get("c")

        if price in (None, 0):
            continue

        alert = Alert(
            source="Finnhub",
            symbol=symbol,
            title="Price Update",
            severity="INFO",
            message=f"Current Price: ${price}",
        )

        send_telegram(format_alert(alert))


if __name__ == "__main__":
    main()