from models.ai_benchmark_case import AIBenchmarkCase
from models.ai_benchmark_result import AIBenchmarkResult
from models.semantic_finding_proposal import SemanticFindingProposal
from models.source_document import SourceDocument
from product.ai_benchmark_quality_evaluator import (
    AIBenchmarkQualityEvaluator,
)


def make_case() -> AIBenchmarkCase:
    return AIBenchmarkCase(
        document=SourceDocument(
            source="SEC",
            source_url="https://www.sec.gov/example",
            title="10-Q",
            text=(
                "The pivotal milestone was delayed. "
                "The company opened a $150 million ATM. "
                "Cash declined to $120 million. "
                "The company updated its office lease."
            ),
        ),
        must_find=(
            "The pivotal milestone was delayed.",
            "The company opened a $150 million ATM.",
        ),
        should_find=(
            "Cash declined to $120 million.",
        ),
        must_not_claim=(
            "The pivotal milestone was accelerated.",
        ),
    )


def make_result(
    statements_and_evidence: tuple[tuple[str, str], ...],
) -> AIBenchmarkResult:
    return AIBenchmarkResult(
        provider="provider",
        model="model",
        proposals=tuple(
            SemanticFindingProposal(
                statement=statement,
                evidence_text=evidence,
            )
            for statement, evidence in statements_and_evidence
        ),
        latency_seconds=1.0,
        input_tokens=1000,
        output_tokens=100,
    )


def test_quality_evaluator_reports_perfect_precision_for_relevant_findings() -> None:
    evaluator = AIBenchmarkQualityEvaluator()

    evaluation = evaluator.evaluate(
        benchmark_case=make_case(),
        result=make_result(
            (
                (
                    "The pivotal milestone was delayed.",
                    "The pivotal milestone was delayed.",
                ),
                (
                    "The company opened a $150 million ATM.",
                    "The company opened a $150 million ATM.",
                ),
                (
                    "Cash declined to $120 million.",
                    "Cash declined to $120 million.",
                ),
            )
        ),
    )

    assert evaluation.finding_precision == 1.0
    assert evaluation.passed_quality_gate


def test_quality_evaluator_penalizes_irrelevant_grounded_noise() -> None:
    evaluator = AIBenchmarkQualityEvaluator()

    evaluation = evaluator.evaluate(
        benchmark_case=make_case(),
        result=make_result(
            (
                (
                    "The pivotal milestone was delayed.",
                    "The pivotal milestone was delayed.",
                ),
                (
                    "The company opened a $150 million ATM.",
                    "The company opened a $150 million ATM.",
                ),
                (
                    "Cash declined to $120 million.",
                    "Cash declined to $120 million.",
                ),
                (
                    "The company updated its office lease.",
                    "The company updated its office lease.",
                ),
            )
        ),
    )

    assert evaluation.finding_precision == 0.75
    assert evaluation.passed_quality_gate
