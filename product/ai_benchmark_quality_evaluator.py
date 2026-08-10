from models.ai_benchmark_case import AIBenchmarkCase
from models.ai_benchmark_quality_evaluation import (
    AIBenchmarkQualityEvaluation,
)
from models.ai_benchmark_result import AIBenchmarkResult


class AIBenchmarkQualityEvaluator:
    def evaluate(
        self,
        benchmark_case: AIBenchmarkCase,
        result: AIBenchmarkResult,
    ) -> AIBenchmarkQualityEvaluation:
        statements = {
            proposal.statement
            for proposal in result.proposals
        }

        must_find_matches = sum(
            1
            for statement in benchmark_case.must_find
            if statement in statements
        )

        should_find_matches = sum(
            1
            for statement in benchmark_case.should_find
            if statement in statements
        )

        must_not_claim_violations = sum(
            1
            for statement in benchmark_case.must_not_claim
            if statement in statements
        )

        must_find_recall = (
            must_find_matches / len(benchmark_case.must_find)
        )

        if benchmark_case.should_find:
            should_find_recall = (
                should_find_matches
                / len(benchmark_case.should_find)
            )
        else:
            should_find_recall = 1.0

        if result.proposals:
            grounded_evidence_count = sum(
                1
                for proposal in result.proposals
                if proposal.evidence_text
                in benchmark_case.document.text
            )
            evidence_fidelity = (
                grounded_evidence_count
                / len(result.proposals)
            )
        else:
            evidence_fidelity = 1.0

        relevant_statements = {
            *benchmark_case.must_find,
            *benchmark_case.should_find,
        }

        if result.proposals:
            relevant_proposal_count = sum(
                1
                for proposal in result.proposals
                if proposal.statement in relevant_statements
            )
            finding_precision = (
                relevant_proposal_count
                / len(result.proposals)
            )
        else:
            finding_precision = 1.0

        passed_quality_gate = (
            must_find_recall == 1.0
            and must_not_claim_violations == 0
            and evidence_fidelity == 1.0
        )

        return AIBenchmarkQualityEvaluation(
            must_find_recall=must_find_recall,
            should_find_recall=should_find_recall,
            must_not_claim_violations=(
                must_not_claim_violations
            ),
            evidence_fidelity=evidence_fidelity,
            finding_precision=finding_precision,
            passed_quality_gate=passed_quality_gate,
        )
