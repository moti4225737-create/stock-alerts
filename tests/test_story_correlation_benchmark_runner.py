from models.event import Event
from models.story_correlation_benchmark_case import (
    StoryCorrelationBenchmarkCase,
)
from models.story_correlation_result import (
    StoryCorrelationResult,
)
from application.story_correlation_benchmark_runner import (
    StoryCorrelationBenchmarkRunner,
)


class StubCorrelator:
    def __init__(
        self,
        results: tuple[StoryCorrelationResult, ...],
    ) -> None:
        self._results = list(results)
        self.calls = 0

    def correlate(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        self.calls += 1
        return self._results.pop(0)


def make_event(
    title: str,
    summary: str,
    published_at: str,
) -> Event:
    return Event(
        symbol="ONDS",
        source="Benchmark",
        title=title,
        summary=summary,
        published_at=published_at,
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


def make_case(
    name: str,
    expected: bool,
) -> StoryCorrelationBenchmarkCase:
    return StoryCorrelationBenchmarkCase(
        name=name,
        earlier_event=make_event(
            title="Earlier event",
            summary="Earlier summary",
            published_at="2026-06-18",
        ),
        current_event=make_event(
            title="Current event",
            summary="Current summary",
            published_at="2026-08-10",
        ),
        expected_is_correlated=expected,
    )


def test_runner_records_expected_and_actual_results() -> None:
    cases = (
        make_case(
            name="positive case",
            expected=True,
        ),
        make_case(
            name="negative case",
            expected=False,
        ),
    )

    correlator = StubCorrelator(
        results=(
            StoryCorrelationResult(
                is_correlated=True,
                confidence=0.9,
                reason="Same story.",
            ),
            StoryCorrelationResult(
                is_correlated=False,
                confidence=0.8,
                reason="Different stories.",
            ),
        )
    )

    runner = StoryCorrelationBenchmarkRunner(
        correlator=correlator,
    )

    results = runner.run(cases)

    assert len(results) == 2
    assert correlator.calls == 2

    assert results[0].case_name == "positive case"
    assert results[0].expected_is_correlated is True
    assert results[0].actual_is_correlated is True
    assert results[0].confidence == 0.9
    assert results[0].passed is True
    assert results[0].reason == "Same story."

    assert results[1].case_name == "negative case"
    assert results[1].expected_is_correlated is False
    assert results[1].actual_is_correlated is False
    assert results[1].confidence == 0.8
    assert results[1].passed is True


def test_runner_marks_wrong_decision_as_failed() -> None:
    case = make_case(
        name="wrong decision",
        expected=True,
    )

    correlator = StubCorrelator(
        results=(
            StoryCorrelationResult(
                is_correlated=False,
                confidence=0.7,
                reason="Incorrect negative.",
            ),
        )
    )

    runner = StoryCorrelationBenchmarkRunner(
        correlator=correlator,
    )

    results = runner.run((case,))

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].expected_is_correlated is True
    assert results[0].actual_is_correlated is False
