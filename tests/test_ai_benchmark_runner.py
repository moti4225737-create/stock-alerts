from unittest.mock import Mock

from application.ai_benchmark_runner import AIBenchmarkRunner
from models.ai_benchmark_case import AIBenchmarkCase
from models.analyzer_execution_result import AnalyzerExecutionResult
from models.semantic_finding_proposal import SemanticFindingProposal
from models.source_document import SourceDocument


def make_case() -> AIBenchmarkCase:
    return AIBenchmarkCase(
        document=SourceDocument(
            source="SEC",
            source_url="https://www.sec.gov/example",
            title="10-Q",
            text="The pivotal milestone was delayed.",
        ),
        must_find=(
            "The pivotal milestone was delayed.",
        ),
        should_find=(),
        must_not_claim=(),
    )


def test_runner_executes_analyzer_and_builds_raw_benchmark_result() -> None:
    analyzer = Mock()
    analyzer.analyze.return_value = AnalyzerExecutionResult(
        proposals=(
            SemanticFindingProposal(
                statement="The pivotal milestone was delayed.",
                evidence_text="The pivotal milestone was delayed.",
            ),
        ),
        input_tokens=120000,
        output_tokens=350,
    )

    times = iter((100.0, 112.5))
    clock = Mock(side_effect=lambda: next(times))

    runner = AIBenchmarkRunner(
        provider="example-provider",
        model="example-model",
        analyzer=analyzer,
        clock=clock,
    )

    benchmark_case = make_case()

    result = runner.run(benchmark_case)

    analyzer.analyze.assert_called_once_with(
        benchmark_case.document
    )

    assert result.provider == "example-provider"
    assert result.model == "example-model"
    assert result.latency_seconds == 12.5
    assert result.input_tokens == 120000
    assert result.output_tokens == 350
    assert len(result.proposals) == 1


def test_runner_preserves_empty_analyzer_result() -> None:
    analyzer = Mock()
    analyzer.analyze.return_value = AnalyzerExecutionResult(
        proposals=(),
        input_tokens=1000,
        output_tokens=0,
    )

    times = iter((10.0, 11.0))
    clock = Mock(side_effect=lambda: next(times))

    runner = AIBenchmarkRunner(
        provider="example-provider",
        model="example-model",
        analyzer=analyzer,
        clock=clock,
    )

    result = runner.run(make_case())

    assert result.proposals == ()
    assert result.latency_seconds == 1.0
    assert result.input_tokens == 1000
    assert result.output_tokens == 0
