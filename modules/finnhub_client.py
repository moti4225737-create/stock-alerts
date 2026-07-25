import os

import requests
from dotenv import load_dotenv


load_dotenv()

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
REQUEST_TIMEOUT_SECONDS = 20


def _get_api_key() -> str:
    """
    Return the Finnhub API key from the environment.

    The key is read only when an API request is made, so importing
    this module does not fail when the environment is not configured.
    """
    api_key = os.getenv("FINNHUB_API_KEY")

    if not api_key:
        raise RuntimeError(
            "FINNHUB_API_KEY is missing. "
            "Add it to the local .env file or GitHub Secrets."
        )

    return api_key


def _get(endpoint: str, params: dict) -> dict:
    """
    Send a GET request to Finnhub and return the JSON response.
    """
    request_params = {
        **params,
        "token": _get_api_key(),
    }

    response = requests.get(
        f"{FINNHUB_BASE_URL}/{endpoint}",
        params=request_params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            f"Unexpected Finnhub response for endpoint: {endpoint}"
        )

    return data


def get_quote(symbol: str) -> dict:
    """
    Fetch the latest market quote for a stock symbol.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise ValueError("Symbol cannot be empty.")

    return _get(
        endpoint="quote",
        params={"symbol": normalized_symbol},
    )


def get_company_profile(symbol: str) -> dict:
    """
    Fetch company profile information for a stock symbol.

    The response can include the company name, exchange, country,
    industry and other identifying information.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise ValueError("Symbol cannot be empty.")

    return _get(
        endpoint="stock/profile2",
        params={"symbol": normalized_symbol},
    )