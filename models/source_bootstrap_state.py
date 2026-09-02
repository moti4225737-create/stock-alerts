from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from models.company_identity import CompanyIdentity
from models.portfolio_holding import PortfolioHolding
from models.source_evidence import SourceEvidence


class SourceBootstrapLifecycle(str, Enum):
    LEARNING = "learning"
    READY = "ready"


class OpeningFactDisposition(str, Enum):
    VERIFIED = "verified"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class OpeningFactCandidate:
    fact: str
    category: str
    evidence: tuple[SourceEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.fact, str) or not self.fact.strip():
            raise ValueError("opening fact is required")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("opening fact category is required")
        if not all(isinstance(value, SourceEvidence) for value in self.evidence):
            raise TypeError("opening fact evidence must contain SourceEvidence")


@dataclass(frozen=True, slots=True)
class OpeningFactDecision:
    candidate: OpeningFactCandidate
    disposition: OpeningFactDisposition

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, OpeningFactCandidate):
            raise TypeError("decision candidate must be an OpeningFactCandidate")
        if not isinstance(self.disposition, OpeningFactDisposition):
            raise TypeError("opening fact disposition is required")


@dataclass(frozen=True, slots=True)
class OpeningResearchResult:
    candidates: tuple[OpeningFactCandidate, ...]
    completed_successfully: bool

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, OpeningFactCandidate) for value in self.candidates
        ):
            raise TypeError(
                "opening research candidates must contain OpeningFactCandidate"
            )
        if len(self.candidates) > 10:
            raise ValueError("opening research cannot exceed 10 candidates")
        if not isinstance(self.completed_successfully, bool):
            raise TypeError("research completion must be boolean")


@dataclass(frozen=True, slots=True)
class SourceBootstrapResearchRequest:
    holding: PortfolioHolding
    time_zero: datetime

    def __post_init__(self) -> None:
        if self.time_zero.tzinfo is None or self.time_zero.utcoffset() is None:
            raise ValueError("time_zero must be timezone-aware")
        object.__setattr__(
            self,
            "time_zero",
            self.time_zero.astimezone(timezone.utc),
        )


@dataclass(frozen=True, slots=True)
class SourceBootstrapState:
    request: SourceBootstrapResearchRequest
    research_output: object | None = None
    verified_identity: CompanyIdentity | None = None
    decisions: tuple[OpeningFactDecision, ...] = ()

    @property
    def time_zero(self) -> datetime:
        return self.request.time_zero

    @property
    def lifecycle(self) -> SourceBootstrapLifecycle:
        if self._opening_is_ready():
            return SourceBootstrapLifecycle.READY
        return SourceBootstrapLifecycle.LEARNING

    @property
    def is_ready(self) -> bool:
        return self.lifecycle is SourceBootstrapLifecycle.READY

    def _opening_is_ready(self) -> bool:
        identity = self.verified_identity
        research = self.research_output
        if (
            not self._is_complete_opening_identity(identity)
            or not isinstance(research, OpeningResearchResult)
            or not research.completed_successfully
        ):
            return False

        candidates = research.candidates
        if len(self.decisions) != len(candidates):
            return False

        decided_candidates = tuple(
            decision.candidate
            for decision in self.decisions
            if isinstance(decision, OpeningFactDecision)
        )
        if len(decided_candidates) != len(self.decisions):
            return False
        if any(
            decided_candidates.count(candidate) != candidates.count(candidate)
            for candidate in candidates
        ):
            return False

        return any(
            decision.disposition is OpeningFactDisposition.VERIFIED
            for decision in self.decisions
        )

    @staticmethod
    def _is_complete_opening_identity(identity: object) -> bool:
        return isinstance(identity, CompanyIdentity) and all(
            isinstance(value, str) and bool(value.strip())
            for value in (
                identity.ticker,
                identity.company_name,
                identity.cik,
                identity.exchange,
            )
        )
