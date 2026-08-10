from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate
from product.source_materiality_evaluator import (
    SourceMaterialityEvaluator,
)


def make_candidate(
    statement: str,
) -> SourceFindingCandidate:
    return SourceFindingCandidate(
        statement=statement,
        evidence=(
            SourceEvidence(
                source_url="https://www.sec.gov/example",
                text=statement,
            ),
        ),
    )


def test_materiality_evaluator_converts_candidate_to_scored_finding() -> None:
    evaluator = SourceMaterialityEvaluator(
        policy={
            "milestone": 10,
            "cash": 8,
            "revenue": 7,
        },
    )

    candidate = make_candidate(
        "The pivotal milestone was delayed."
    )

    finding = evaluator.evaluate(candidate)

    assert finding.statement == candidate.statement
    assert finding.evidence == candidate.evidence
    assert finding.materiality == 10


def test_materiality_evaluator_uses_default_score_when_no_rule_matches() -> None:
    evaluator = SourceMaterialityEvaluator(
        policy={
            "milestone": 10,
        },
        default_materiality=5,
    )

    candidate = make_candidate(
        "The company updated its corporate presentation."
    )

    finding = evaluator.evaluate(candidate)

    assert finding.materiality == 5
