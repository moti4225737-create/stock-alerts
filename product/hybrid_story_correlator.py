from typing import Protocol

from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationResult,
)


class StoryCorrelatorProtocol(Protocol):
    def correlate(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        ...


class HybridStoryCorrelator:
    def __init__(
        self,
        deterministic_correlator: StoryCorrelatorProtocol,
        semantic_correlator: StoryCorrelatorProtocol,
    ) -> None:
        self._deterministic_correlator = (
            deterministic_correlator
        )
        self._semantic_correlator = semantic_correlator

    def correlate(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        deterministic_result = (
            self._deterministic_correlator.correlate(
                earlier_event=earlier_event,
                current_event=current_event,
            )
        )

        if deterministic_result.is_resolved:
            return deterministic_result

        return self._semantic_correlator.correlate(
            earlier_event=earlier_event,
            current_event=current_event,
        )
