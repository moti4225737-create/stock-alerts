from dataclasses import dataclass


@dataclass(frozen=True)
class AIBenchmarkQualityEvaluation:
    must_find_recall: float
    should_find_recall: float
    must_not_claim_violations: int
    evidence_fidelity: float
    finding_precision: float
    passed_quality_gate: bool
