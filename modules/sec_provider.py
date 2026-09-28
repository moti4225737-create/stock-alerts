from dataclasses import replace
import os
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import requests

from models.event import Event
from models.source_observation import SourceObservationState
from modules.data_provider import DataProvider


from modules.source_observation_lifecycle import ManagedSourceObservationProvider
class SECProvider(DataProvider, ManagedSourceObservationProvider):
    """
    Fetches recent company filings from the official SEC EDGAR API.
    """

    SOURCE_NAME = "SEC"
    TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
    FILING_URL = (
        "https://www.sec.gov/Archives/edgar/data/"
        "{cik}/{accession_without_dashes}/{primary_document}"
    )

    IMPORTANT_FORMS = {
        "8-K",
        "10-Q",
        "10-K",
        "6-K",
        "20-F",
    }

    def __init__(
        self, timeout: int = 20, max_events: int = 10,
        *, time_zero_for: Callable[[str], datetime | None] | None = None,
        source_observation_store: object | None = None,
    ):
        self._time_zero_for = time_zero_for
        self._source_observation_store = source_observation_store
        self._exposed_pending: dict[str, set[str]] = {}
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
        return self._fetch_filings(symbol, opening_evidence=False)

    def fetch_opening_evidence(self, symbol: str) -> list[Event]:
        """Acquire official filing context without live admission or state writes."""
        return self._fetch_filings(symbol, opening_evidence=True)

    def _fetch_filings(
        self, symbol: str, *, opening_evidence: bool,
    ) -> list[Event]:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            return []

        existing = None
        if not opening_evidence and self._source_observation_store is not None:
            existing = self._source_observation_store.load(
                source=self.SOURCE_NAME, scope=normalized_symbol,
            )
            if existing is not None and existing.pending:
                replay = self._replay_pending(normalized_symbol, existing)
                if replay:
                    self._exposed_pending.setdefault(normalized_symbol, set()).update(
                        event.event_id for event in replay
                    )
                    return replay

        cik = self._get_cik(normalized_symbol)
        submissions = self._get_submissions(cik)
        recent_filings = submissions.get("filings", {}).get("recent", {})

        forms = recent_filings.get("form", [])
        filing_dates = recent_filings.get("filingDate", [])
        acceptance_times = recent_filings.get("acceptanceDateTime", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        primary_documents = recent_filings.get("primaryDocument", [])
        descriptions = recent_filings.get("primaryDocDescription", [])

        observation_scope = normalized_symbol
        objects = dict(existing.objects) if existing is not None else {}
        events: list[Event] = []

        time_zero = (
            self._time_zero_for(normalized_symbol)
            if not opening_evidence and self._time_zero_for is not None
            else None
        )

        for index, form in enumerate(forms):
            if form not in self.IMPORTANT_FORMS:
                continue

            filing_date = self._safe_list_value(filing_dates, index)
            acceptance_time = self._safe_list_value(acceptance_times, index)
            accession_number = self._safe_list_value(accession_numbers, index)
            primary_document = self._safe_list_value(primary_documents, index)
            description = self._safe_list_value(descriptions, index)

            object_id = accession_number or (
                f"{form}|{filing_date}|{primary_document}"
            )

            previous_object = objects.get(object_id)

            objects[object_id] = {
                "form": form,
                "filing_date": filing_date,
                "acceptance_datetime": acceptance_time,
                "accession_number": accession_number,
                "primary_document": primary_document,
                "description": description,
            }

            occurrence_time = self._parse_occurrence_time(acceptance_time)
            if not opening_evidence and (
                occurrence_time is None
                or time_zero is None
                or time_zero.tzinfo is None
                or occurrence_time < time_zero.astimezone(timezone.utc)
            ):
                continue

            filing_url = self._build_filing_url(
                cik=cik,
                accession_number=accession_number,
                primary_document=primary_document,
            )
            summary = description or f"SEC filing submitted on {filing_date}"
            event_id = (
                f"{self.SOURCE_NAME}|{accession_number}"
                if accession_number
                else None
            )
            if event_id is None:
                continue

            if (
                not opening_evidence
                and previous_object == objects[object_id]
            ):
                continue

            if not opening_evidence and len(events) >= self.max_events:
                raise ValueError("SEC acquisition exceeded the event cap")

            events.append(Event(
                symbol=normalized_symbol,
                source=self.SOURCE_NAME,
                title=f"SEC Filing: {form}",
                summary=summary,
                published_at=filing_date,
                importance=1,
                sentiment="neutral",
                url=filing_url,
                event_id=event_id,
            ))

            if opening_evidence and len(events) >= self.max_events:
                break

        if not opening_evidence and self._source_observation_store is not None:
            retained = existing.pending if existing is not None else ()
            retained_ids = {item.get("event_id") for item in retained}
            pending = retained + tuple(
                self._serialize_pending_event(event)
                for event in events if event.event_id not in retained_ids
            )
            self._source_observation_store.save(
                SourceObservationState(
                    schema="stock-sentinel.source-observation",
                    version=1,
                    source=self.SOURCE_NAME,
                    scope=observation_scope,
                    objects=dict(sorted(objects.items())),
                    pending=pending,
                    observed_through=None,
                )
            )

            self._exposed_pending.setdefault(normalized_symbol, set()).update(
                event.event_id for event in events
            )

        return events

    def begin_attempt(self) -> None:
        self._exposed_pending.clear()

    def _replay_pending(
        self, symbol: str, state: SourceObservationState,
    ) -> list[Event]:
        time_zero = self._time_zero_for(symbol) if self._time_zero_for else None
        if time_zero is None or time_zero.tzinfo is None:
            return []
        events = []
        for pending in state.pending:
            event_id = pending.get("event_id")
            if (
                not isinstance(event_id, str)
                or not event_id.startswith("SEC|")
                or pending.get("source") != self.SOURCE_NAME
                or pending.get("symbol") != symbol
            ):
                continue
            record = state.objects.get(event_id[len("SEC|"):], {})
            occurrence = self._parse_occurrence_time(record.get("acceptance_datetime", ""))
            if occurrence is not None and occurrence >= time_zero.astimezone(timezone.utc):
                events.append(Event(**pending))
        return events

    def acknowledge_pending(self) -> None:
        if self._source_observation_store is None:
            return
        for scope, exposed in list(self._exposed_pending.items()):
            current = self._source_observation_store.load(
                source=self.SOURCE_NAME, scope=scope,
            )
            if current is not None:
                remaining = tuple(
                    pending for pending in current.pending
                    if pending.get("event_id") not in exposed
                )
                if remaining != current.pending:
                    self._source_observation_store.save(
                        replace(current, pending=remaining)
                    )
            self._exposed_pending.pop(scope, None)

    @staticmethod
    def _parse_occurrence_time(value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _serialize_pending_event(event: Event) -> dict:
        return {
            "event_id": event.event_id,
            "symbol": event.symbol,
            "source": event.source,
            "title": event.title,
            "summary": event.summary,
            "published_at": event.published_at,
            "importance": event.importance,
            "sentiment": event.sentiment,
            "url": event.url,
        }

    def _get_cik(self, symbol: str) -> str:
        if self._ticker_to_cik is None:
            self._ticker_to_cik = self._load_ticker_mapping()

        cik = self._ticker_to_cik.get(symbol)

        if not cik:
            raise ValueError(f"SEC CIK was not found for symbol: {symbol}")

        return cik

    def _load_ticker_mapping(self) -> dict[str, str]:
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
        if not accession_number or not primary_document:
            return None

        return self.FILING_URL.format(
            cik=str(int(cik)),
            accession_without_dashes=accession_number.replace("-", ""),
            primary_document=primary_document,
        )

    @staticmethod
    def _safe_list_value(values: list[Any], index: int) -> str:
        if index >= len(values):
            return ""

        value = values[index]

        if value is None:
            return ""

        return str(value)
