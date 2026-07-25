from typing import Any

import requests

from models.event import Event
from modules.data_provider import DataProvider
from modules.openfda_client import OpenFDAClient
from modules.ticker_resolver import TickerResolver


class FDAProvider(DataProvider):
    """
    Collect FDA drug recall intelligence for public companies.

    The provider resolves a ticker symbol into a company identity,
    searches the official openFDA drug enforcement endpoint,
    and converts matching recall records into Event objects.
    """

    RECALL_URL = (
        "https://www.accessdata.fda.gov/scripts/ires/"
        "index.cfm"
    )

    def __init__(
        self,
        client: OpenFDAClient | None = None,
        ticker_resolver: TickerResolver | None = None,
        max_events: int = 10,
    ) -> None:
        if max_events < 1:
            raise ValueError("max_events must be at least 1")

        self.client = client or OpenFDAClient()
        self.ticker_resolver = ticker_resolver or TickerResolver()
        self.max_events = max_events

    def fetch_events(self, symbol: str) -> list[Event]:
        """
        Fetch recent FDA drug recall events for one stock symbol.

        Returns an empty list when:
        - the symbol is empty
        - the company identity cannot be resolved
        - openFDA returns no matching records
        - the openFDA request fails
        """
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            return []

        identity = self.ticker_resolver.get_company_identity(
            normalized_symbol
        )

        if identity is None:
            return []

        company_name = self._prepare_company_search_name(
            identity.company_name
        )

        if not company_name:
            return []

        query = self._build_recall_query(company_name)

        try:
            records = self.client.search_drug_enforcement(
                query=query,
                limit=self.max_events,
            )
        except (
            requests.RequestException,
            RuntimeError,
            ValueError,
            OSError,
        ):
            return []

        events: list[Event] = []

        for record in records:
            event = self._record_to_event(
                symbol=normalized_symbol,
                record=record,
            )

            if event is not None:
                events.append(event)

        return events

    @staticmethod
    def _prepare_company_search_name(company_name: str) -> str:
        """
        Prepare a company name for use in an openFDA search.

        Common public-company suffixes are removed because recall
        records may use a shorter operational company name.
        """
        cleaned_name = company_name.strip()

        suffixes = (
            " Corporation",
            " Incorporated",
            " Corp.",
            " Corp",
            " Inc.",
            " Inc",
            " Ltd.",
            " Ltd",
            " Limited",
            " PLC",
            " N.V.",
            " S.A.",
        )

        for suffix in suffixes:
            if cleaned_name.lower().endswith(suffix.lower()):
                cleaned_name = cleaned_name[
                    : -len(suffix)
                ].strip()
                break

        return cleaned_name

    @staticmethod
    def _build_recall_query(company_name: str) -> str:
        """
        Build an openFDA search expression for the recalling firm.
        """
        escaped_name = company_name.replace(
            "\\",
            "\\\\",
        ).replace(
            '"',
            '\\"',
        )

        return f'recalling_firm:"{escaped_name}"'

    def _record_to_event(
        self,
        symbol: str,
        record: dict[str, Any],
    ) -> Event | None:
        """
        Convert one openFDA drug enforcement record into an Event.
        """
        recalling_firm = self._clean_string(
            record.get("recalling_firm")
        )
        reason = self._clean_string(
            record.get("reason_for_recall")
        )
        product_description = self._clean_string(
            record.get("product_description")
        )
        recall_number = self._clean_string(
            record.get("recall_number")
        )
        classification = self._clean_string(
            record.get("classification")
        )
        status = self._clean_string(
            record.get("status")
        )
        published_at = (
            self._clean_string(
                record.get("report_date")
            )
            or self._clean_string(
                record.get("recall_initiation_date")
            )
            or ""
        )

        if not recalling_firm and not reason:
            return None

        title_parts = ["FDA Drug Recall"]

        if classification:
            title_parts.append(classification)

        if recalling_firm:
            title_parts.append(recalling_firm)

        title = " — ".join(title_parts)

        summary_parts: list[str] = []

        if reason:
            summary_parts.append(reason)

        if product_description:
            summary_parts.append(
                f"Product: {product_description}"
            )

        if recall_number:
            summary_parts.append(
                f"Recall number: {recall_number}"
            )

        if status:
            summary_parts.append(
                f"Status: {status}"
            )

        summary = " | ".join(summary_parts)

        if not summary:
            summary = "FDA drug recall enforcement record."

        return Event(
            symbol=symbol,
            source="FDA",
            title=title,
            summary=summary,
            published_at=published_at,
            importance=1,
            sentiment="negative",
            url=self.RECALL_URL,
        )

    @staticmethod
    def _clean_string(value: object) -> str | None:
        """
        Return a stripped string or None for invalid values.
        """
        if not isinstance(value, str):
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            return None

        return cleaned_value