from enum import Enum


class StoryCorrelationDecision(str, Enum):
    MATCH = "match"
    NO_MATCH = "no_match"
    UNRESOLVED = "unresolved"


class StoryCorrelationResult:
    __slots__ = (
        "decision",
        "confidence",
        "reason",
    )

    def __init__(
        self,
        *,
        confidence: float,
        reason: str,
        decision: StoryCorrelationDecision | None = None,
        is_correlated: bool | None = None,
    ) -> None:
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if not reason.strip():
            raise ValueError("reason is required")

        if (
            decision is not None
            and is_correlated is not None
        ):
            raise ValueError(
                "provide either decision or is_correlated, "
                "not both"
            )

        if decision is None:
            if is_correlated is None:
                raise ValueError(
                    "decision or is_correlated is required"
                )

            decision = (
                StoryCorrelationDecision.MATCH
                if is_correlated
                else StoryCorrelationDecision.NO_MATCH
            )

        if (
            decision
            is StoryCorrelationDecision.UNRESOLVED
            and confidence == 1.0
        ):
            raise ValueError(
                "unresolved result cannot have full confidence"
            )

        self.decision = decision
        self.confidence = confidence
        self.reason = reason

    @property
    def is_correlated(self) -> bool:
        return (
            self.decision
            is StoryCorrelationDecision.MATCH
        )

    @property
    def is_resolved(self) -> bool:
        return (
            self.decision
            is not StoryCorrelationDecision.UNRESOLVED
        )

    def __repr__(self) -> str:
        return (
            "StoryCorrelationResult("
            f"decision={self.decision!r}, "
            f"confidence={self.confidence!r}, "
            f"reason={self.reason!r}"
            ")"
        )
