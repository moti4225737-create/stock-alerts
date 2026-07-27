from collections.abc import Callable
from datetime import date, datetime
from typing import Optional

import requests

from models.event import Event
from modules.clinical_trials_client import ClinicalTrialsClient
from modules.data_provider import DataProvider
from modules.ticker_resolver import TickerResolver


class ClinicalTrialsProvider(DataProvider):
    """
    Convert ClinicalTrials.gov studies into normalized Event objects.
    """

    SOURCE_NAME = "ClinicalTrials.gov"
    STUDY_BASE_URL = "https://clinicaltrials.gov/study"

    def __init__(
        self,
        client: Optional[ClinicalTrialsClient] = None,
        ticker_resolver: Optional[TickerResolver] = None,
        max_events: int = 10,
        max_age_days: int = 90,
        today_provider: Optional[Callable[[], date]] = None,
    ) -> None:
        if max_events < 1:
            raise ValueError("max_events must be at least 1")

        if max_age_days < 1:
            raise ValueError("max_age_days must be at least 1")

        self._client = client or ClinicalTrialsClient()
        self._ticker_resolver = (
            ticker_resolver or TickerResolver()
        )
        self._max_events = max_events
        self._max_age_days = max_age_days
        self._today_provider = today_provider or date.today

    def fetch_events(self, symbol: str) -> list[Event]:
        """
        Fetch recent clinical studies associated with a ticker symbol.

        The ticker is resolved into a company identity, the company
        name is prepared for sponsor search, and recent valid studies
        are converted into Event objects.
        """
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            return []

        identity = self._ticker_resolver.get_company_identity(
            normalized_symbol
        )

        if identity is None:
            return []

        search_name = (
            self._ticker_resolver.prepare_company_search_name(
                identity.company_name
            )
        )

        if not search_name:
            return []

        try:
            studies = self._client.search_studies(
                query=search_name,
                page_size=self._max_events,
            )
        except requests.RequestException:
            return []

        events: list[Event] = []

        for study in studies:
            event = self._study_to_event(
                symbol=normalized_symbol,
                study=study,
            )

            if event is not None:
                events.append(event)

        return events

    def _study_to_event(
        self,
        symbol: str,
        study: dict,
    ) -> Optional[Event]:
        """
        Convert one recent ClinicalTrials.gov study into an Event.

        A study must contain an NCT identifier, a brief title,
        and a recent publication or update date.
        """
        if not isinstance(study, dict):
            return None

        protocol_section = study.get("protocolSection")

        if not isinstance(protocol_section, dict):
            return None

        identification_module = protocol_section.get(
            "identificationModule"
        )

        if not isinstance(identification_module, dict):
            return None

        nct_id = self._clean_string(
            identification_module.get("nctId")
        )
        brief_title = self._clean_string(
            identification_module.get("briefTitle")
        )

        if nct_id is None or brief_title is None:
            return None

        status_module = protocol_section.get("statusModule")

        if not isinstance(status_module, dict):
            status_module = {}

        overall_status = self._clean_string(
            status_module.get("overallStatus")
        )

        published_at = self._extract_date(
            status_module.get(
                "lastUpdatePostDateStruct"
            )
        )

        if published_at is None:
            published_at = self._extract_date(
                status_module.get(
                    "studyFirstPostDateStruct"
                )
            )

        if not self._is_recent(published_at):
            return None

        conditions = self._extract_conditions(
            protocol_section.get("conditionsModule")
        )

        brief_summary = self._extract_brief_summary(
            protocol_section.get("descriptionModule")
        )

        summary_parts: list[str] = []

        if brief_summary is not None:
            summary_parts.append(brief_summary)

        summary_parts.append(f"NCT ID: {nct_id}")

        if overall_status is not None:
            summary_parts.append(
                f"Status: {overall_status}"
            )

        if conditions:
            summary_parts.append(
                f"Conditions: {', '.join(conditions)}"
            )

        return Event(
            symbol=symbol,
            source=self.SOURCE_NAME,
            title=f"Clinical Trial — {brief_title}",
            summary=" | ".join(summary_parts),
            published_at=published_at,
            importance=2,
            sentiment="neutral",
            url=f"{self.STUDY_BASE_URL}/{nct_id}",
        )

    def _is_recent(
        self,
        published_at: Optional[str],
    ) -> bool:
        """
        Return True when the study date is within the freshness window.
        """
        if published_at is None:
            return False

        parsed_date = self._parse_date(published_at)

        if parsed_date is None:
            return False

        age_days = (
            self._today_provider() - parsed_date
        ).days

        return 0 <= age_days <= self._max_age_days

    @staticmethod
    def _parse_date(value: str) -> Optional[date]:
        """
        Parse supported ClinicalTrials.gov date formats.
        """
        formats = (
            "%Y-%m-%d",
            "%Y-%m",
            "%Y",
        )

        for date_format in formats:
            try:
                return datetime.strptime(
                    value,
                    date_format,
                ).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def _extract_date(value: object) -> Optional[str]:
        """
        Extract a date string from a ClinicalTrials.gov date structure.
        """
        if not isinstance(value, dict):
            return None

        return ClinicalTrialsProvider._clean_string(
            value.get("date")
        )

    @staticmethod
    def _extract_conditions(value: object) -> list[str]:
        """
        Extract and clean the list of study conditions.
        """
        if not isinstance(value, dict):
            return []

        raw_conditions = value.get("conditions")

        if not isinstance(raw_conditions, list):
            return []

        conditions: list[str] = []

        for condition in raw_conditions:
            cleaned_condition = (
                ClinicalTrialsProvider._clean_string(
                    condition
                )
            )

            if cleaned_condition is not None:
                conditions.append(cleaned_condition)

        return conditions

    @staticmethod
    def _extract_brief_summary(
        value: object,
    ) -> Optional[str]:
        """
        Extract the brief study summary when available.
        """
        if not isinstance(value, dict):
            return None

        return ClinicalTrialsProvider._clean_string(
            value.get("briefSummary")
        )

    @staticmethod
    def _clean_string(value: object) -> Optional[str]:
        """
        Return a stripped string or None for invalid and empty values.
        """
        if not isinstance(value, str):
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            return None

        return cleaned_value