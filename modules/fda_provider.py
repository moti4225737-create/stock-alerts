from dataclasses import replace
from typing import Any

from collections.abc import Callable
from datetime import datetime, timezone

from models.event import Event
from models.source_observation import SourceObservationState
from modules.data_provider import DataProvider
from modules.source_observation_lifecycle import ManagedSourceObservationProvider
from modules.openfda_client import OpenFDAClient
from modules.ticker_resolver import TickerResolver


class FDAProvider(DataProvider, ManagedSourceObservationProvider):
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

    SOURCE_NAME = "FDA"

    def __init__(
        self,
        client: OpenFDAClient | None = None,
        ticker_resolver: TickerResolver | None = None,
        max_events: int = 10,
        time_zero_for: Callable[[str], datetime | None] | None = None,
        source_observation_store: object | None = None,
    ) -> None:
        if max_events < 1:
            raise ValueError("max_events must be at least 1")

        self.client = client or OpenFDAClient()
        self.ticker_resolver = ticker_resolver or TickerResolver()
        self.max_events = max_events
        self._time_zero_for = time_zero_for
        self._source_observation_store = source_observation_store
        self._exposed_pending: dict[str, set[str]] = {}

    def fetch_events(self, symbol: str) -> list[Event]:
        """
        Fetch recent FDA drug recall events for one stock symbol.
        """
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            return []

        existing = None
        if self._source_observation_store is not None:
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

        identity = self.ticker_resolver.get_company_identity(
            normalized_symbol
        )

        if identity is None:
            return []

        company_name = (
            self.ticker_resolver.prepare_company_search_name(
                identity.company_name
            )
        )

        if not company_name:
            return []

        query = self._build_recall_query(company_name)

        records = self.client.search_drug_enforcement(
            query=query,
            limit=self.max_events,
        )

        observation_enabled = (
            self._source_observation_store is not None
        )

        objects = dict(existing.objects) if existing is not None else {}

        time_zero = None
        if self._time_zero_for is not None:
            time_zero = self._time_zero_for(normalized_symbol)

        events: list[Event] = []

        for record in records:
            event = self._record_to_event(
                symbol=normalized_symbol,
                record=record,
            )

            if event is None:
                continue

            recall_number = self._clean_string(
                record.get("recall_number")
            )

            object_id = (
                recall_number
                or self._fallback_object_id(record)
            )

            if observation_enabled:
                previous_object = objects.get(object_id)
                current_object = dict(record)
                objects[object_id] = current_object

                if previous_object == current_object:
                    continue

                occurrence_time = self._authoritative_occurrence_time(
                    record
                )

                if (
                    occurrence_time is None
                    or time_zero is None
                    or time_zero.tzinfo is None
                    or occurrence_time
                    < time_zero.astimezone(timezone.utc)
                ):
                    continue

            event_id = (
                f"{self.SOURCE_NAME}|recall|{recall_number}"
                if recall_number
                else None
            )

            if event_id is None:
                if observation_enabled:
                    continue
            else:
                event = Event(
                    symbol=event.symbol,
                    source=event.source,
                    title=event.title,
                    summary=event.summary,
                    published_at=event.published_at,
                    importance=event.importance,
                    sentiment=event.sentiment,
                    url=event.url,
                    event_id=event_id,
                )

            events.append(event)

        if observation_enabled:
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
                    scope=normalized_symbol,
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
                or not event_id.startswith("FDA|recall|")
                or pending.get("source") != self.SOURCE_NAME
                or pending.get("symbol") != symbol
            ):
                continue
            record = state.objects.get(event_id[len("FDA|recall|"):], {})
            occurrence = self._authoritative_occurrence_time(record)
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
            source=self.SOURCE_NAME,
            title=title,
            summary=summary,
            published_at=published_at,
            importance=1,
            sentiment="negative",
            url=self.RECALL_URL,
        )

    @classmethod
    def _authoritative_occurrence_time(
        cls,
        record: dict[str, Any],
    ) -> datetime | None:
        report_date = cls._clean_string(
            record.get("report_date")
        )

        if report_date is None:
            return None

        try:
            parsed = datetime.strptime(
                report_date,
                "%Y%m%d",
            )
        except ValueError:
            return None

        return parsed.replace(tzinfo=timezone.utc)

    @classmethod
    def _fallback_object_id(
        cls,
        record: dict[str, Any],
    ) -> str:
        return "|".join(
            [
                cls._clean_string(
                    record.get("recalling_firm")
                ) or "",
                cls._clean_string(
                    record.get("report_date")
                ) or "",
                cls._clean_string(
                    record.get("product_description")
                ) or "",
            ]
        )

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
