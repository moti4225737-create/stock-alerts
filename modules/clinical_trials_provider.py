from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Optional

import requests

from models.asset import Asset
from models.asset_kind import AssetKind
from models.asset_registry import AssetRegistry
from models.company_asset_link import CompanyAssetLink
from models.company_asset_registry import CompanyAssetRegistry
from models.company_asset_relationship import (
    CompanyAssetRelationship,
)
from models.company_identity import CompanyIdentity
from models.event import Event
from models.source_observation import SourceObservationState
from modules.clinical_trials_client import ClinicalTrialsClient
from modules.data_provider import DataProvider
from modules.source_observation_lifecycle import ManagedSourceObservationProvider
from modules.ticker_resolver import TickerResolver


class ClinicalTrialsProvider(DataProvider, ManagedSourceObservationProvider):
    """
    Convert ClinicalTrials.gov studies into normalized Event objects
    and enrich the company-asset knowledge base.
    """

    SOURCE_NAME = "ClinicalTrials.gov"
    STUDY_BASE_URL = "https://clinicaltrials.gov/study"

    def __init__(
        self,
        client: Optional[ClinicalTrialsClient] = None,
        ticker_resolver: Optional[TickerResolver] = None,
        asset_registry: Optional[AssetRegistry] = None,
        company_asset_registry: Optional[
            CompanyAssetRegistry
        ] = None,
        max_events: int = 10,
        max_age_days: int = 90,
        today_provider: Optional[Callable[[], date]] = None,
        source_observation_store: object | None = None,
        time_zero_for: Callable[[str], datetime | None] | None = None,
    ) -> None:
        if max_events < 1:
            raise ValueError("max_events must be at least 1")

        if max_age_days < 1:
            raise ValueError("max_age_days must be at least 1")

        self._client = client or ClinicalTrialsClient()
        self._ticker_resolver = (
            ticker_resolver or TickerResolver()
        )
        self._asset_registry = (
            asset_registry
            if asset_registry is not None
            else AssetRegistry()
        )
        self._company_asset_registry = (
            company_asset_registry
            if company_asset_registry is not None
            else CompanyAssetRegistry()
        )
        self._max_events = max_events
        self._max_age_days = max_age_days
        self._today_provider = today_provider or date.today
        self._source_observation_store = source_observation_store
        self._time_zero_for = time_zero_for
        self._exposed_pending: dict[str, tuple[str, ...]] = {}

    def fetch_events(self, symbol: str) -> list[Event]:
        """
        Fetch recent clinical studies associated with a ticker symbol.

        The ticker is resolved into a company identity, the company
        name is prepared for sponsor search, and recent valid studies
        are converted into Event objects and knowledge-base links.
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

        existing_observation = None
        observation_scope = None
        if self._source_observation_store is not None:
            observation_scope = f"{normalized_symbol}:{search_name.casefold()}"
            existing_observation = self._source_observation_store.load(
                source=self.SOURCE_NAME,
                scope=observation_scope,
            )
            if (
                existing_observation is not None
                and existing_observation.pending
            ):
                replayable_pending = tuple(
                    persisted_event
                    for persisted_event in existing_observation.pending
                    if self._pending_is_live_for_current_lifecycle(
                        normalized_symbol,
                        persisted_event,
                    )
                )
                if replayable_pending:
                    self._exposed_pending[observation_scope] = tuple(
                        persisted_event["event_id"]
                        for persisted_event in replayable_pending
                    )
                    return [
                        Event(**persisted_event)
                        for persisted_event in replayable_pending
                    ]
                if replayable_pending != existing_observation.pending:
                    existing_observation = SourceObservationState(
                        schema=existing_observation.schema,
                        version=existing_observation.version,
                        source=existing_observation.source,
                        scope=existing_observation.scope,
                        objects=existing_observation.objects,
                        pending=(),
                        observed_through=existing_observation.observed_through,
                    )
                    self._source_observation_store.save(existing_observation)

        if self._source_observation_store is not None:
            is_bootstrap = (
                existing_observation is None
                or existing_observation.observed_through is None
            )
            if is_bootstrap:
                studies = self._acquire_complete_observation(
                    search_name=search_name,
                )
            else:
                lower_bound = (
                    date.fromisoformat(existing_observation.observed_through)
                    - timedelta(days=1)
                )
                query_term = (
                    f'AREA[SponsorSearch]"{search_name}" AND '
                    f'AREA[LastUpdatePostDate]RANGE[{lower_bound.isoformat()}, MAX]'
                )
                studies = self._acquire_complete_observation(
                    query_term=query_term,
                )
            if studies is None:
                raise requests.RequestException(
                    "ClinicalTrials acquisition did not complete"
                )
        else:
            try:
                studies = self._client.search_studies(
                    query=search_name,
                    page_size=self._max_events,
                )
            except requests.RequestException:
                raise

        if self._source_observation_store is not None:
            scope = observation_scope
            existing = existing_observation
            objects = self._canonical_observation(studies)
            observed_through = self._today_provider().isoformat()
            if existing is None or existing.observed_through is None:
                events = []
                if self._time_zero_for is not None:
                    events = self._new_study_events(
                        symbol=normalized_symbol,
                        studies=studies,
                        previous_objects={},
                        current_objects=objects,
                    )
                    events = self._live_events_only(
                        normalized_symbol,
                        events,
                    )
                initial_state = SourceObservationState(
                    schema="stock-sentinel.source-observation",
                    version=1,
                    source=self.SOURCE_NAME,
                    scope=scope,
                    objects=objects,
                    pending=tuple(
                        self._serialize_pending_event(event)
                        for event in events
                    ),
                    observed_through=observed_through,
                )
                self._source_observation_store.save(initial_state)
                self._exposed_pending[scope] = tuple(
                    persisted_event["event_id"]
                    for persisted_event in initial_state.pending
                )
                return events
            events = self._status_transition_events(
                symbol=normalized_symbol,
                studies=studies,
                previous_objects=existing.objects,
                current_objects=objects,
            )
            events.extend(self._new_study_events(
                symbol=normalized_symbol,
                studies=studies,
                previous_objects=existing.objects,
                current_objects=objects,
            ))
            events = self._live_events_only(
                normalized_symbol,
                events,
            )
            merged_objects = dict(existing.objects)
            merged_objects.update(objects)
            advanced_state = SourceObservationState(
                schema=existing.schema,
                version=existing.version,
                source=existing.source,
                scope=existing.scope,
                objects=dict(sorted(merged_objects.items())),
                pending=tuple(
                    self._serialize_pending_event(event)
                    for event in events
                ),
                observed_through=observed_through,
            )
            self._source_observation_store.save(advanced_state)
            self._exposed_pending[scope] = tuple(
                persisted_event["event_id"]
                for persisted_event in advanced_state.pending
            )
            return events

        events: list[Event] = []

        for study in studies:
            event = self._study_to_event(
                symbol=normalized_symbol,
                study=study,
            )

            if event is not None:
                events.append(event)
                self._register_study_assets(
                    identity=identity,
                    study=study,
                )

        return events

    def _acquire_complete_observation(
        self,
        *,
        search_name: str | None = None,
        query_term: str | None = None,
    ) -> list[dict] | None:
        studies: list[dict] = []
        next_page_token: str | None = None
        while True:
            try:
                query_arguments = (
                    {"query_term": query_term}
                    if query_term is not None
                    else {"query": search_name}
                )
                if next_page_token is None:
                    page = self._client.search_studies(
                        **query_arguments,
                        page_size=self._max_events,
                    )
                else:
                    page = self._client.search_studies(
                        **query_arguments,
                        page_size=self._max_events,
                        page_token=next_page_token,
                    )
            except (requests.RequestException, ValueError):
                raise

            studies.extend(page)
            next_page_token = getattr(page, "next_page_token", None)
            if next_page_token is None:
                return studies

    def acknowledge_pending(self) -> None:
        if self._source_observation_store is None:
            return

        acknowledged_scopes: list[str] = []
        for scope, exposed_event_ids in self._exposed_pending.items():
            current = self._source_observation_store.load(
                source=self.SOURCE_NAME,
                scope=scope,
            )
            if current is None:
                continue
            exposed = set(exposed_event_ids)
            remaining = tuple(
                persisted_event
                for persisted_event in current.pending
                if persisted_event.get("event_id") not in exposed
            )
            if remaining != current.pending:
                self._source_observation_store.save(
                    SourceObservationState(
                        schema=current.schema,
                        version=current.version,
                        source=current.source,
                        scope=current.scope,
                        objects=current.objects,
                        pending=remaining,
                        observed_through=current.observed_through,
                    )
                )
            acknowledged_scopes.append(scope)

        for scope in acknowledged_scopes:
            self._exposed_pending.pop(scope, None)

    @classmethod
    def _status_transition_events(
        cls,
        *,
        symbol: str,
        studies: list[dict],
        previous_objects: dict[str, dict],
        current_objects: dict[str, dict],
    ) -> list[Event]:
        studies_by_nct_id: dict[str, dict] = {}
        for study in studies:
            if not isinstance(study, dict):
                continue
            protocol = study.get("protocolSection")
            if not isinstance(protocol, dict):
                continue
            identification = protocol.get("identificationModule")
            if not isinstance(identification, dict):
                continue
            nct_id = cls._clean_string(identification.get("nctId"))
            if nct_id is not None:
                studies_by_nct_id[nct_id.upper()] = study

        events: list[Event] = []
        for nct_id in sorted(previous_objects.keys() & current_objects.keys()):
            previous_status = previous_objects[nct_id].get("overall_status")
            current_status = current_objects[nct_id].get("overall_status")
            if previous_status == current_status:
                continue

            study = studies_by_nct_id.get(nct_id, {})
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            title = cls._clean_string(identification.get("briefTitle")) or nct_id
            published_at = (
                cls._extract_date(status.get("lastUpdatePostDateStruct"))
                or ""
            )
            before = previous_status or "UNKNOWN"
            after = current_status or "UNKNOWN"
            base_event_id = (
                f"{cls.SOURCE_NAME}|{nct_id}|overall_status|"
                f"{before}|{after}"
            )
            occurrence_date = cls._extract_date(
                status.get("lastUpdatePostDateStruct")
            )
            event_id = (
                f"{base_event_id}|{occurrence_date}"
                if occurrence_date
                else base_event_id
            )
            events.append(Event(
                symbol=symbol,
                source=cls.SOURCE_NAME,
                title=f"Clinical Trial — {title}",
                summary=(
                    f"NCT ID: {nct_id} | Overall status changed: "
                    f"{before} → {after}"
                ),
                published_at=published_at,
                importance=2,
                sentiment="neutral",
                url=f"{cls.STUDY_BASE_URL}/{nct_id}",
                event_id=event_id,
            ))
        return events

    def _new_study_events(
        self,
        *,
        symbol: str,
        studies: list[dict],
        previous_objects: dict[str, dict],
        current_objects: dict[str, dict],
    ) -> list[Event]:
        new_ids = current_objects.keys() - previous_objects.keys()
        events: list[Event] = []
        for study in studies:
            event = self._study_to_event(symbol=symbol, study=study)
            if event is None:
                continue
            nct_id = event.url.rsplit("/", 1)[-1].upper()
            if nct_id not in new_ids:
                continue

            protocol = study.get("protocolSection", {})
            status = protocol.get("statusModule", {})
            first_post_date = self._extract_date(
                status.get("studyFirstPostDateStruct")
            )

            event.published_at = first_post_date or ""
            event.event_id = f"{self.SOURCE_NAME}|{nct_id}|new_study"
            events.append(event)
        return events

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

    @classmethod
    def _canonical_observation(cls, studies: list[dict]) -> dict[str, dict]:
        objects: dict[str, dict] = {}
        for study in studies:
            if not isinstance(study, dict):
                continue
            protocol = study.get("protocolSection")
            if not isinstance(protocol, dict):
                continue
            identification = protocol.get("identificationModule")
            if not isinstance(identification, dict):
                continue
            nct_id = cls._clean_string(identification.get("nctId"))
            if nct_id is None:
                continue

            status = protocol.get("statusModule")
            status = status if isinstance(status, dict) else {}
            design = protocol.get("designModule")
            design = design if isinstance(design, dict) else {}
            enrollment = design.get("enrollmentInfo")
            enrollment = enrollment if isinstance(enrollment, dict) else {}
            interventions = protocol.get("armsInterventionsModule")
            interventions = interventions if isinstance(interventions, dict) else {}
            outcomes = protocol.get("outcomesModule")
            outcomes = outcomes if isinstance(outcomes, dict) else {}
            results = study.get("resultsSection")

            objects[nct_id.upper()] = {
                "overall_status": cls._clean_string(status.get("overallStatus")),
                "why_stopped": cls._clean_string(status.get("whyStopped")),
                "phases": cls._canonical_strings(design.get("phases")),
                "enrollment": {
                    "count": enrollment.get("count"),
                    "type": cls._clean_string(enrollment.get("type")),
                },
                "start_date": cls._canonical_date(status.get("startDateStruct")),
                "primary_completion_date": cls._canonical_date(
                    status.get("primaryCompletionDateStruct")
                ),
                "completion_date": cls._canonical_date(
                    status.get("completionDateStruct")
                ),
                "interventions": cls._canonical_interventions(
                    interventions.get("interventions")
                ),
                "primary_outcomes": cls._canonical_primary_outcomes(
                    outcomes.get("primaryOutcomes")
                ),
                "results_first_post_date": cls._extract_date(
                    status.get("resultsFirstPostDateStruct")
                ),
                "results_fingerprint": cls._results_fingerprint(results),
            }
        return dict(sorted(objects.items()))

    @classmethod
    def _canonical_strings(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return sorted({cleaned for item in value if (cleaned := cls._clean_string(item))})

    @classmethod
    def _canonical_date(cls, value: object) -> dict[str, Optional[str]]:
        if not isinstance(value, dict):
            return {"date": None, "type": None}
        return {
            "date": cls._clean_string(value.get("date")),
            "type": cls._clean_string(value.get("type")),
        }

    @classmethod
    def _canonical_interventions(cls, value: object) -> list[list[str]]:
        if not isinstance(value, list):
            return []
        canonical = set()
        for item in value:
            if not isinstance(item, dict):
                continue
            kind = cls._clean_string(item.get("type"))
            name = cls._clean_string(item.get("name"))
            if kind is not None and name is not None:
                canonical.add((kind, name))
        return [list(item) for item in sorted(canonical)]

    @classmethod
    def _canonical_primary_outcomes(cls, value: object) -> list[list[str]]:
        if not isinstance(value, list):
            return []
        canonical = set()
        for item in value:
            if not isinstance(item, dict):
                continue
            measure = cls._clean_string(item.get("measure"))
            timeframe = cls._clean_string(item.get("timeFrame"))
            if measure is not None:
                canonical.add((measure, timeframe or ""))
        return [list(item) for item in sorted(canonical)]

    @staticmethod
    def _results_fingerprint(value: object) -> Optional[str]:
        if not isinstance(value, dict):
            return None
        canonical = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

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

    def _live_events_only(
        self,
        symbol: str,
        events: list[Event],
    ) -> list[Event]:
        time_zero = (
            self._time_zero_for(symbol)
            if self._time_zero_for is not None
            else None
        )
        if time_zero is None:
            return events
        if time_zero.tzinfo is None:
            return []
        boundary = time_zero.astimezone(timezone.utc)
        return [
            event
            for event in events
            if (
                (occurrence := self._exact_occurrence_time(
                    event.published_at
                )) is not None
                and occurrence >= boundary
            )
        ]

    def _pending_is_live_for_current_lifecycle(
        self,
        symbol: str,
        persisted_event: dict,
    ) -> bool:
        time_zero = (
            self._time_zero_for(symbol)
            if self._time_zero_for is not None
            else None
        )
        if time_zero is None:
            return True
        if time_zero.tzinfo is None:
            return False
        occurrence = self._exact_occurrence_time(
            persisted_event.get("published_at")
        )
        return (
            occurrence is not None
            and occurrence >= time_zero.astimezone(timezone.utc)
        )

    @staticmethod
    def _exact_occurrence_time(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None
        return parsed.replace(tzinfo=timezone.utc)
    def _register_study_assets(
        self,
        identity: CompanyIdentity,
        study: dict,
    ) -> None:
        """
        Register supported study interventions as company assets.
        """
        protocol_section = study.get("protocolSection")

        if not isinstance(protocol_section, dict):
            return

        interventions_module = protocol_section.get(
            "armsInterventionsModule"
        )

        if not isinstance(interventions_module, dict):
            return

        interventions = interventions_module.get(
            "interventions"
        )

        if not isinstance(interventions, list):
            return

        for intervention in interventions:
            self._register_intervention(
                identity=identity,
                intervention=intervention,
            )

    def _register_intervention(
        self,
        identity: CompanyIdentity,
        intervention: object,
    ) -> None:
        """
        Register one supported ClinicalTrials intervention.
        """
        if not isinstance(intervention, dict):
            return

        intervention_type = self._clean_string(
            intervention.get("type")
        )
        name = self._clean_string(
            intervention.get("name")
        )

        if intervention_type != "DRUG" or name is None:
            return

        aliases = self._extract_aliases(
            intervention.get("otherNames"),
            primary_name=name,
        )

        asset = self._find_registered_asset(
            name=name,
            aliases=aliases,
        )

        if asset is None:
            asset = Asset(
                name=name,
                kind=AssetKind.DRUG,
                aliases=aliases,
            )
            self._asset_registry.register(asset)

        link = CompanyAssetLink(
            company=identity,
            asset=asset,
            relationship=CompanyAssetRelationship.DEVELOPS,
        )
        self._company_asset_registry.register(link)

    def _find_registered_asset(
        self,
        name: str,
        aliases: tuple[str, ...],
    ) -> Optional[Asset]:
        """
        Find an existing canonical asset by name or alias.
        """
        for identifier in (name, *aliases):
            asset = self._asset_registry.find_by_name(
                identifier
            )

            if asset is not None:
                return asset

        return None

    @classmethod
    def _extract_aliases(
        cls,
        value: object,
        primary_name: str,
    ) -> tuple[str, ...]:
        """
        Extract unique aliases while preserving source order.
        """
        if not isinstance(value, list):
            return ()

        aliases: list[str] = []
        normalized_identifiers = {
            primary_name.casefold(),
        }

        for raw_alias in value:
            alias = cls._clean_string(raw_alias)

            if alias is None:
                continue

            normalized_alias = alias.casefold()

            if normalized_alias in normalized_identifiers:
                continue

            aliases.append(alias)
            normalized_identifiers.add(normalized_alias)

        return tuple(aliases)

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
