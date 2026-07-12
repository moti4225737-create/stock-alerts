import os
import requests

# Environment Variables
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
FINNHUB_API_KEY = os.environ["FINNHUB_API_KEY"]

# Stock to test
SYMBOL = "AAPL"

# Finnhub Quote API
quote = requests.get(
    f"https://finnhub.io/api/v1/quote?symbol={SYMBOL}&token={FINNHUB_API_KEY}"
).json()

print(quote)

price = quote["c"]
change = quote["d"]
percent = quote["dp"]

message = f"""
📈 Stock Sentinel

Symbol: {SYMBOL}

Price: ${price}

Change: {change}

Percent: {percent}%
"""

# Telegram
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

requests.post(
    url,
    data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
)

print("Stock alert sent.")
