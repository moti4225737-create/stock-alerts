from dataclasses import dataclass

from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationDecision,
)


@dataclass(frozen=True, slots=True)
class SemanticStoryBenchmarkCase:
    name: str
    earlier_event: Event
    current_event: Event
    expected_decision: StoryCorrelationDecision

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name is required")


@dataclass(frozen=True, slots=True)
class SemanticStoryBenchmarkResult:
    case_name: str
    expected: StoryCorrelationDecision
    actual: StoryCorrelationDecision
    confidence: float
    reason: str

    @property
    def passed(self) -> bool:
        return self.expected is self.actual


class SemanticStoryBenchmarkEvaluator:
    @staticmethod
    def is_correct(
        expected: StoryCorrelationDecision,
        actual: StoryCorrelationDecision,
    ) -> bool:
        return expected is actual

    def evaluate(
        self,
        case_name: str,
        expected: StoryCorrelationDecision,
        actual: StoryCorrelationDecision,
        confidence: float,
        reason: str,
    ) -> SemanticStoryBenchmarkResult:
        return SemanticStoryBenchmarkResult(
            case_name=case_name,
            expected=expected,
            actual=actual,
            confidence=confidence,
            reason=reason,
        )
