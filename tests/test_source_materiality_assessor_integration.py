from unittest.mock import Mock

from models.significance_assessment import (
    SignificanceAssessment,
    SignificanceDecision,
)
from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate
from product.source_materiality_evaluator import (
    SourceMaterialityEvaluator,
)


def make_candidate() -> SourceFindingCandidate:
    statement = (
        "The pivotal milestone was delayed."
    )

    return SourceFindingCandidate(
        statement=statement,
        evidence=(
            SourceEvidence(
                source_url="https://www.sec.gov/example",
                text=statement,
            ),
        ),
    )


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="8-K",
        text="The pivotal milestone was delayed.",
    )


def test_materiality_evaluator_uses_significance_assessor() -> None:
    assessor = Mock()

    assessment = SignificanceAssessment(
        decision=SignificanceDecision.ASSESSED,
        significance=9,
        confidence=0.94,
        rationale=(
            "The delay changes the expected timing "
            "of a pivotal milestone."
        ),
    )

    assessor.assess.return_value = assessment

    evaluator = SourceMaterialityEvaluator(
        assessor=assessor,
    )

    candidate = make_candidate()
    document = make_document()

    finding = evaluator.evaluate(
        candidate,
        document,
    )

    assert finding.statement == candidate.statement
    assert finding.evidence == candidate.evidence
    assert finding.materiality == 9

    assessor.assess.assert_called_once_with(
        candidate,
        document,
    )
