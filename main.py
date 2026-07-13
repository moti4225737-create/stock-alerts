import os
import requests

from watchlist import WATCHLIST

# Environment Variables
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
FINNHUB_API_KEY = os.environ["FINNHUB_API_KEY"]

message = "📈 Stock Sentinel\n\n"

for symbol in WATCHLIST:
    try:
        url = (
            f"https://finnhub.io/api/v1/quote"
            f"?symbol={symbol}&token={FINNHUB_API_KEY}"
        )

        quote = requests.get(url, timeout=15).json()

        if "c" not in quote:
            message += f"{symbol}: No data\n"
            continue

        price = quote["c"]
        change = quote["d"]
        percent = quote["dp"]

        message += (
            f"{symbol}\n"
            f"Price: ${price}\n"
            f"Change: {change}\n"
            f"Percent: {percent}%\n\n"
        )

    except Exception as e:
        message += f"{symbol}: ERROR ({e})\n\n"

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

requests.post(
    telegram_url,
    data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    },
    timeout=15
)

print("Message sent.")
