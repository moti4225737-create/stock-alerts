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


class SemanticStoryBenchmarkEvaluator:
    @staticmethod
    def is_correct(
        expected: StoryCorrelationDecision,
        actual: StoryCorrelationDecision,
    ) -> bool:
        return expected is actual
