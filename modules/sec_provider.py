import os
from typing import Any

import requests

from models.event import Event
from modules.data_provider import DataProvider


class SECProvider(DataProvider):
    """
    Fetches recent company filings from the official SEC EDGAR API.
    """

    TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
    FILING_URL = (
        "https://www.sec.gov/Archives/edgar/data/"
        "{cik}/{accession_without_dashes}/{primary_document}"
    )

    IMPORTANT_FORMS = {
        "8-K": 8,
        "10-Q": 7,
        "10-K": 8,
        "6-K": 8,
        "20-F": 8,
    }

    def __init__(self, timeout: int = 20, max_events: int = 10):
        self.timeout = timeout
        self.max_events = max_events

        user_agent = os.getenv("SEC_USER_AGENT")

        if not user_agent:
            raise ValueError(
                "SEC_USER_AGENT is missing. "
                "Add it to the .env file before using SECProvider."
            )

        self.headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
        }

        self._ticker_to_cik: dict[str, str] | None = None

    def fetch_events(self, symbol: str) -> list[Event]:
        """
        Fetch recent important SEC filings for one stock symbol.

        Args:
            symbol: Stock ticker, for example AAPL.

        Returns:
            List of Event objects.
        """
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            return []

        cik = self._get_cik(normalized_symbol)
        submissions = self._get_submissions(cik)
        recent_filings = submissions.get("filings", {}).get("recent", {})

        forms = recent_filings.get("form", [])
        filing_dates = recent_filings.get("filingDate", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        primary_documents = recent_filings.get("primaryDocument", [])
        descriptions = recent_filings.get("primaryDocDescription", [])

        events: list[Event] = []

        for index, form in enumerate(forms):
            if form not in self.IMPORTANT_FORMS:
                continue

            filing_date = self._safe_list_value(filing_dates, index)
            accession_number = self._safe_list_value(
                accession_numbers,
                index,
            )
            primary_document = self._safe_list_value(
                primary_documents,
                index,
            )
            description = self._safe_list_value(descriptions, index)

            filing_url = self._build_filing_url(
                cik=cik,
                accession_number=accession_number,
                primary_document=primary_document,
            )

            summary = description or f"SEC filing submitted on {filing_date}"

            event = Event(
                symbol=normalized_symbol,
                source="SEC",
                title=f"SEC Filing: {form}",
                summary=summary,
                published_at=filing_date,
                importance=self.IMPORTANT_FORMS[form],
                sentiment="neutral",
                url=filing_url,
            )

            events.append(event)

            if len(events) >= self.max_events:
                break

        return events

    def _get_cik(self, symbol: str) -> str:
        """
        Convert a stock ticker to its zero-padded SEC CIK.
        """
        if self._ticker_to_cik is None:
            self._ticker_to_cik = self._load_ticker_mapping()

        cik = self._ticker_to_cik.get(symbol)

        if not cik:
            raise ValueError(f"SEC CIK was not found for symbol: {symbol}")

        return cik

    def _load_ticker_mapping(self) -> dict[str, str]:
        """
        Download the official SEC ticker-to-CIK mapping.
        """
        response = requests.get(
            self.TICKERS_URL,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()

        ticker_data = response.json()
        ticker_to_cik: dict[str, str] = {}

        for company in ticker_data.values():
            ticker = str(company.get("ticker", "")).upper()
            cik_number = company.get("cik_str")

            if not ticker or cik_number is None:
                continue

            ticker_to_cik[ticker] = str(cik_number).zfill(10)

        return ticker_to_cik

    def _get_submissions(self, cik: str) -> dict[str, Any]:
        """
        Download recent SEC submissions for one CIK.
        """
        url = self.SUBMISSIONS_URL.format(cik=cik)

        response = requests.get(
            url,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()

        return response.json()

    def _build_filing_url(
        self,
        cik: str,
        accession_number: str,
        primary_document: str,
    ) -> str | None:
        """
        Build the public EDGAR URL for a filing document.
        """
        if not accession_number or not primary_document:
            return None

        return self.FILING_URL.format(
            cik=str(int(cik)),
            accession_without_dashes=accession_number.replace("-", ""),
            primary_document=primary_document,
        )

    @staticmethod
    def _safe_list_value(values: list[Any], index: int) -> str:
        """
        Safely read a value from one of the SEC parallel data arrays.
        """
        if index >= len(values):
            return ""

        value = values[index]

        if value is None:
            return ""

        return str(value)