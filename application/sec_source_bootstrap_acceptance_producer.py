from collections.abc import Callable
from urllib.parse import SplitResult, urlsplit

from models.company_identity import CompanyIdentity
from models.event import Event
from models.source_bootstrap_state import (
    OpeningFactCandidate,
    OpeningFactDecision,
    OpeningFactDisposition,
    OpeningResearchResult,
    SourceBootstrapState,
)
from models.source_document import SourceDocument
from models.source_finding_candidate import SourceFindingCandidate
from product.source_evidence_validator import SourceEvidenceValidator


class SECSourceBootstrapAcceptanceProducer:
    """Independently verify Opening fact candidates against SEC truth."""

    _SEC_HOST = "www.sec.gov"
    _ARCHIVE_PREFIX = "/Archives/edgar/data/"

    def __init__(
        self,
        *,
        official_event_discovery: Callable[[str], object],
        document_reconstruction: Callable[[Event], object],
        finding_discovery: Callable[[SourceDocument], object],
        max_distinct_verification_targets: int | None = None,
    ) -> None:
        if (
            max_distinct_verification_targets is not None
            and (
                isinstance(max_distinct_verification_targets, bool)
                or not isinstance(max_distinct_verification_targets, int)
            )
        ):
            raise TypeError(
                "max_distinct_verification_targets must be an integer"
            )
        if (
            max_distinct_verification_targets is not None
            and max_distinct_verification_targets < 0
        ):
            raise ValueError(
                "max_distinct_verification_targets must not be negative"
            )
        self._official_event_discovery = official_event_discovery
        self._document_reconstruction = document_reconstruction
        self._finding_discovery = finding_discovery
        self._evidence_validator = SourceEvidenceValidator()
        self._max_distinct_verification_targets = (
            max_distinct_verification_targets
        )

    def __call__(
        self,
        state: SourceBootstrapState,
    ) -> tuple[OpeningFactDecision, ...]:
        research_output = state.research_output
        identity = state.verified_identity
        candidates = (
            research_output.candidates
            if isinstance(research_output, OpeningResearchResult)
            else ()
        )

        verified_by_key: dict[
            tuple[str, str, str], OpeningFactDisposition
        ] = {}
        distinct_verification_targets = 0
        decisions: list[OpeningFactDecision] = []
        identity_is_complete = self._is_complete_identity(identity)
        for candidate in candidates:
            key = (
                self._verification_key(candidate)
                if identity_is_complete
                else None
            )
            reused_disposition = (
                verified_by_key.get(key) if key is not None else None
            )
            if reused_disposition is None:
                if key is not None:
                    budget_exhausted = (
                        self._max_distinct_verification_targets is not None
                        and distinct_verification_targets
                        >= self._max_distinct_verification_targets
                    )
                    if budget_exhausted:
                        disposition = OpeningFactDisposition.UNRESOLVED
                    else:
                        distinct_verification_targets += 1
                        disposition = self._disposition(candidate, identity)
                    verified_by_key[key] = disposition
                else:
                    disposition = OpeningFactDisposition.UNRESOLVED
            else:
                disposition = reused_disposition
            decisions.append(OpeningFactDecision(
                candidate=candidate,
                disposition=disposition,
            ))
        return tuple(decisions)

    def _verification_key(
        self,
        candidate: OpeningFactCandidate,
    ) -> tuple[str, str, str] | None:
        proposed_url = self._candidate_sec_url(candidate)
        if proposed_url is None:
            return None
        return (
            "SEC",
            proposed_url.path,
            self._normalize_statement(candidate.fact),
        )

    def _disposition(
        self,
        candidate: OpeningFactCandidate,
        identity: CompanyIdentity,
    ) -> OpeningFactDisposition:
        proposed_url = self._candidate_sec_url(candidate)
        if proposed_url is None:
            return OpeningFactDisposition.UNRESOLVED

        symbol = identity.ticker.strip().upper()
        try:
            discovered = self._official_event_discovery(symbol)
            events = tuple(discovered)
        except Exception:
            return OpeningFactDisposition.UNRESOLVED

        matches = tuple(
            event
            for event in events
            if self._event_matches(event, proposed_url)
        )
        if len(matches) != 1:
            return OpeningFactDisposition.UNRESOLVED

        event = matches[0]
        if not self._event_belongs_to_identity(event, identity):
            return OpeningFactDisposition.UNRESOLVED

        try:
            reconstructed = self._document_reconstruction(event)
        except Exception:
            return OpeningFactDisposition.UNRESOLVED
        if (
            not isinstance(reconstructed, SourceDocument)
            or not reconstructed.text.strip()
        ):
            return OpeningFactDisposition.UNRESOLVED

        try:
            discovered_findings = tuple(
                self._finding_discovery(reconstructed)
            )
        except Exception:
            return OpeningFactDisposition.UNRESOLVED

        statement_hint = self._normalize_statement(candidate.fact)
        matching_findings = tuple(
            finding
            for finding in discovered_findings
            if isinstance(finding, SourceFindingCandidate)
            and self._normalize_statement(finding.statement)
            == statement_hint
            and self._evidence_validator.is_valid(reconstructed, finding)
        )
        if len(matching_findings) != 1:
            return OpeningFactDisposition.UNRESOLVED

        return OpeningFactDisposition.VERIFIED

    def _candidate_sec_url(
        self,
        candidate: OpeningFactCandidate,
    ) -> SplitResult | None:
        if candidate.category.strip().lower() != "sec_filing":
            return None
        urls = tuple(
            parsed
            for evidence in candidate.evidence
            if (parsed := self._strict_sec_url(evidence.source_url))
            is not None
        )
        unique_paths = {url.path for url in urls}
        if len(unique_paths) != 1:
            return None
        return urls[0]

    @classmethod
    def _is_complete_identity(cls, value: object) -> bool:
        return (
            isinstance(value, CompanyIdentity)
            and all(
                isinstance(field, str) and bool(field.strip())
                for field in (
                    value.ticker,
                    value.company_name,
                    value.cik,
                    value.exchange,
                )
            )
            and cls._normalize_cik(value.cik) is not None
        )

    def _event_matches(
        self,
        event: object,
        proposed_url: SplitResult,
    ) -> bool:
        if not isinstance(event, Event) or event.url is None:
            return False
        official_url = self._strict_sec_url(event.url)
        return (
            official_url is not None
            and official_url.path == proposed_url.path
        )

    def _event_belongs_to_identity(
        self,
        event: Event,
        identity: CompanyIdentity,
    ) -> bool:
        if event.symbol.strip().upper() != identity.ticker.strip().upper():
            return False
        if event.source.strip().upper() != "SEC" or event.url is None:
            return False

        parsed = self._strict_sec_url(event.url)
        identity_cik = self._normalize_cik(identity.cik)
        if parsed is None or identity_cik is None:
            return False

        suffix = parsed.path.removeprefix(self._ARCHIVE_PREFIX)
        if suffix == parsed.path:
            return False
        cik_segment, separator, _ = suffix.partition("/")
        event_cik = self._normalize_cik(cik_segment)
        return bool(separator) and event_cik == identity_cik

    @classmethod
    def _strict_sec_url(cls, value: object) -> SplitResult | None:
        if not isinstance(value, str):
            return None
        try:
            parsed = urlsplit(value.strip())
            port = parsed.port
        except ValueError:
            return None

        if parsed.scheme.lower() != "https":
            return None
        if parsed.hostname is None or parsed.hostname.lower() != cls._SEC_HOST:
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        if port not in (None, 443) or parsed.query:
            return None
        if not parsed.path.startswith(cls._ARCHIVE_PREFIX):
            return None
        return parsed

    @staticmethod
    def _normalize_cik(value: object) -> str | None:
        if value is None:
            return None
        cik = str(value).strip()
        if not cik.isdigit() or len(cik) > 10:
            return None
        return cik.zfill(10)

    @staticmethod
    def _normalize_statement(value: str) -> str:
        return " ".join(value.split())
