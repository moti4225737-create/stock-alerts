from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from models.company_identity import CompanyIdentity
from models.source_bootstrap_state import (
    OpeningFactCandidate,
    OpeningResearchResult,
    SourceBootstrapResearchRequest,
)
from models.source_evidence import SourceEvidence


@dataclass(frozen=True, slots=True)
class BoundedResearchLimits:
    max_candidates: int
    max_document_characters: int

    def __post_init__(self) -> None:
        for name, value in (
            ("max_candidates", self.max_candidates),
            ("max_document_characters", self.max_document_characters),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must not be negative")
        if self.max_candidates > 10:
            raise ValueError("max_candidates must not exceed 10")


@dataclass(frozen=True, slots=True)
class GroundedResearchContext:
    symbol: str
    time_zero: datetime
    known_identity: CompanyIdentity


class SourceBootstrapDomainConversionError(ValueError):
    SAFE_REASONS = {
        "research limit exceeded": "RESEARCH_LIMIT_EXCEEDED",
        "candidate conversion invalid": "CANDIDATE_INVALID",
        "candidate limit exceeded": "CANDIDATE_LIMIT_EXCEEDED",
    }
    SAFE_MESSAGES = frozenset(SAFE_REASONS)

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message
            if message in self.SAFE_MESSAGES
            else "grounded research domain conversion failed"
        )
        self._category = "DOMAIN_CONVERSION"
        self._reason = self.SAFE_REASONS.get(message, "DOMAIN_CONVERSION")

    @property
    def category(self) -> str:
        return self._category

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def response_received(self) -> None:
        return None

    @property
    def status_code(self) -> None:
        return None

class BoundedSourceBootstrapResearcher:
    def __init__(
        self,
        *,
        transport: Callable[[GroundedResearchContext], object],
        limits: BoundedResearchLimits,
    ) -> None:
        self._transport = transport
        self._limits = limits

    def __call__(
        self,
        request: SourceBootstrapResearchRequest,
        *,
        known_identity: CompanyIdentity,
    ) -> OpeningResearchResult:
        context = GroundedResearchContext(
            symbol=request.holding.symbol,
            time_zero=request.time_zero,
            known_identity=known_identity,
        )
        result = self._transport(context)
        try:
            return self._convert(result)
        except SourceBootstrapDomainConversionError:
            raise
        except ValueError as exc:
            raise SourceBootstrapDomainConversionError(str(exc)) from None

    def _convert(
        self,
        result: object,
    ) -> OpeningResearchResult:
        payload = self._classified_conversion(
            lambda: self._mapping(result, "research result"),
            "candidate conversion invalid",
        )
        if set(payload) != {"candidates"}:
            raise SourceBootstrapDomainConversionError(
                "candidate conversion invalid"
            )
        candidates = self._classified_conversion(
            lambda: self._sequence(
                payload.get("candidates"),
                "candidates",
            ),
            "candidate conversion invalid",
        )
        if len(candidates) > self._limits.max_candidates:
            raise SourceBootstrapDomainConversionError(
                "candidate limit exceeded"
            )

        converted_candidates = self._classified_conversion(
            lambda: tuple(
                self._candidate(value) for value in candidates
            ),
            "candidate conversion invalid",
        )

        document_characters = sum(
            len(evidence.text)
            for candidate in converted_candidates
            for evidence in candidate.evidence
        )
        if document_characters > self._limits.max_document_characters:
            raise SourceBootstrapDomainConversionError(
                "research limit exceeded"
            )

        return OpeningResearchResult(
            candidates=converted_candidates,
            completed_successfully=True,
        )

    @staticmethod
    def _classified_conversion(
        operation: Callable[[], object],
        family_message: str,
    ) -> object:
        try:
            return operation()
        except SourceBootstrapDomainConversionError:
            raise
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            message = str(exc)
            if message in SourceBootstrapDomainConversionError.SAFE_MESSAGES:
                raise SourceBootstrapDomainConversionError(message) from None
            raise SourceBootstrapDomainConversionError(
                family_message
            ) from None

    @classmethod
    def _candidate(cls, value: object) -> OpeningFactCandidate:
        payload = cls._mapping(value, "candidate")
        if set(payload) != {"fact", "category", "evidence"}:
            raise ValueError("candidate must contain only approved fields")
        return OpeningFactCandidate(
            fact=payload["fact"],
            category=payload["category"],
            evidence=tuple(
                cls._evidence(item)
                for item in cls._sequence(payload["evidence"], "evidence")
            ),
        )

    @classmethod
    def _evidence(cls, value: object) -> SourceEvidence:
        payload = cls._mapping(value, "evidence")
        return SourceEvidence(
            source_url=payload["source_url"],
            text=payload["text"],
            locator=payload.get("locator"),
        )

    @staticmethod
    def _mapping(value: object, name: str) -> Mapping:
        if not isinstance(value, Mapping):
            raise ValueError(f"{name} must be an object")
        return value

    @staticmethod
    def _sequence(value: object, name: str) -> Sequence:
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise ValueError(f"{name} must be an array")
        return value
