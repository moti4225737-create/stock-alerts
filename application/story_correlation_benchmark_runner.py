from typing import Protocol

from models.event import Event
from models.story_correlation_benchmark_case import (
    StoryCorrelationBenchmarkCase,
)
from models.story_correlation_benchmark_result import (
    StoryCorrelationBenchmarkResult,
)
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


class StoryCorrelationBenchmarkRunner:
    def __init__(
        self,
        correlator: StoryCorrelatorProtocol,
    ) -> None:
        self._correlator = correlator

    def run(
        self,
        cases: tuple[
            StoryCorrelationBenchmarkCase,
            ...,
        ],
    ) -> tuple[
        StoryCorrelationBenchmarkResult,
        ...,
    ]:
        results = []

        for case in cases:
            correlation = self._correlator.correlate(
                earlier_event=case.earlier_event,
                current_event=case.current_event,
            )

            results.append(
                StoryCorrelationBenchmarkResult(
                    case_name=case.name,
                    expected_is_correlated=(
                        case.expected_is_correlated
                    ),
                    actual_is_correlated=(
                        correlation.is_correlated
                    ),
                    confidence=correlation.confidence,
                    reason=correlation.reason,
                )
            )

        return tuple(results)
