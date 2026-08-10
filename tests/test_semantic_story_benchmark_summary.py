from models.story_correlation_result import (
    StoryCorrelationDecision,
)
from product.semantic_story_benchmark_evaluator import (
    SemanticStoryBenchmarkEvaluator,
)


def result(
    name: str,
    expected: StoryCorrelationDecision,
    actual: StoryCorrelationDecision,
):
    return SemanticStoryBenchmarkEvaluator().evaluate(
        case_name=name,
        expected=expected,
        actual=actual,
        confidence=0.95,
        reason="Benchmark result.",
    )


def test_summarize_counts_passed_and_failed_results() -> None:
    evaluator = SemanticStoryBenchmarkEvaluator()

    results = (
        result(
            "match",
            StoryCorrelationDecision.MATCH,
            StoryCorrelationDecision.MATCH,
        ),
        result(
            "no match",
            StoryCorrelationDecision.NO_MATCH,
            StoryCorrelationDecision.NO_MATCH,
        ),
        result(
            "wrong decision",
            StoryCorrelationDecision.UNRESOLVED,
            StoryCorrelationDecision.MATCH,
        ),
    )

    summary = evaluator.summarize(results)

    assert summary.total == 3
    assert summary.passed == 2
    assert summary.failed == 1
    assert summary.pass_rate == 2 / 3


def test_summarize_empty_results_has_zero_pass_rate() -> None:
    evaluator = SemanticStoryBenchmarkEvaluator()

    summary = evaluator.summarize(())

    assert summary.total == 0
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.pass_rate == 0.0
