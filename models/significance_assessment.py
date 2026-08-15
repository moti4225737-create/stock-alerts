from dataclasses import dataclass
from enum import Enum


class SignificanceDecision(str, Enum):
    ASSESSED = "assessed"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class SignificanceAssessment:
    decision: SignificanceDecision
    significance: int | None
    confidence: float
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.decision,
            SignificanceDecision,
        ):
            raise ValueError(
                "decision must be a SignificanceDecision"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if not self.rationale.strip():
            raise ValueError(
                "rationale is required"
            )

        if self.decision is SignificanceDecision.ASSESSED:
            if self.significance is None:
                raise ValueError(
                    "assessed decision requires significance"
                )

            if not 1 <= self.significance <= 10:
                raise ValueError(
                    "significance must be between 1 and 10"
                )

        if self.decision is SignificanceDecision.UNRESOLVED:
            if self.significance is not None:
                raise ValueError(
                    "unresolved decision cannot have significance"
                )
