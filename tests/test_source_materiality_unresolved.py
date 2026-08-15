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


def test_materiality_evaluator_abstains_on_unresolved_assessment() -> None:
    statement = "The company disclosed a new development."

    candidate = SourceFindingCandidate(
        statement=statement,
        evidence=(
            SourceEvidence(
                source_url="https://www.sec.gov/example",
                text=statement,
            ),
        ),
    )

    document = SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="8-K",
        text=statement,
    )

    assessor = Mock()
    assessor.assess.return_value = SignificanceAssessment(
        decision=SignificanceDecision.UNRESOLVED,
        significance=None,
        confidence=0.91,
        rationale=(
            "The source does not provide enough context "
            "to assess investor significance reliably."
        ),
    )

    evaluator = SourceMaterialityEvaluator(
        assessor=assessor,
    )

    assert evaluator.evaluate(
        candidate,
        document,
    ) is None
