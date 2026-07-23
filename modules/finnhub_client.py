import os
import requests

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

FINNHUB_API_KEY = os.environ["FINNHUB_API_KEY"]


def get_quote(symbol):
    url = (
        f"https://finnhub.io/api/v1/quote"
        f"?symbol={symbol}&token={FINNHUB_API_KEY}"
    )

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    return response.json()