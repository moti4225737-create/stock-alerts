from typing import Protocol

from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationResult,
)


class SemanticStoryAnalyzer(Protocol):
    def analyze(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        ...


class SemanticStoryCorrelator:
    def __init__(
        self,
        analyzer: SemanticStoryAnalyzer,
    ) -> None:
        self._analyzer = analyzer

    def correlate(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        return self._analyzer.analyze(
            earlier_event=earlier_event,
            current_event=current_event,
        )
