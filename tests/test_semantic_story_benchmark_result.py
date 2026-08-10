from models.story_correlation_result import (
    StoryCorrelationDecision,
)
from product.semantic_story_benchmark_evaluator import (
    SemanticStoryBenchmarkEvaluator,
)


def test_evaluator_returns_structured_result_for_correct_decision() -> None:
    evaluator = SemanticStoryBenchmarkEvaluator()

    result = evaluator.evaluate(
        case_name="same acquisition continuation",
        expected=StoryCorrelationDecision.MATCH,
        actual=StoryCorrelationDecision.MATCH,
        confidence=0.97,
        reason="The later event completes the same transaction.",
    )

    assert result.case_name == "same acquisition continuation"
    assert result.expected is StoryCorrelationDecision.MATCH
    assert result.actual is StoryCorrelationDecision.MATCH
    assert result.confidence == 0.97
    assert result.reason == (
        "The later event completes the same transaction."
    )
    assert result.passed is True


def test_evaluator_returns_failed_result_for_wrong_decision() -> None:
    evaluator = SemanticStoryBenchmarkEvaluator()

    result = evaluator.evaluate(
        case_name="insufficient identity",
        expected=StoryCorrelationDecision.UNRESOLVED,
        actual=StoryCorrelationDecision.MATCH,
        confidence=0.99,
        reason="The events appear related.",
    )

    assert result.expected is StoryCorrelationDecision.UNRESOLVED
    assert result.actual is StoryCorrelationDecision.MATCH
    assert result.passed is False


def test_evaluator_preserves_high_confidence_unresolved_decision() -> None:
    evaluator = SemanticStoryBenchmarkEvaluator()

    result = evaluator.evaluate(
        case_name="generic financing",
        expected=StoryCorrelationDecision.UNRESOLVED,
        actual=StoryCorrelationDecision.UNRESOLVED,
        confidence=0.98,
        reason=(
            "The evidence is insufficient to establish "
            "transaction identity."
        ),
    )

    assert result.passed is True
    assert result.confidence == 0.98
