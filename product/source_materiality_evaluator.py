from typing import Protocol

from models.significance_assessment import (
    SignificanceAssessment,
    SignificanceDecision,
)
from models.source_document import SourceDocument
from models.source_finding import SourceFinding
from models.source_finding_candidate import SourceFindingCandidate


class SignificanceAssessor(Protocol):
    def assess(
        self,
        candidate: SourceFindingCandidate,
        document: SourceDocument,
    ) -> SignificanceAssessment:
        ...


class SourceMaterialityEvaluator:
    def __init__(
        self,
        assessor: SignificanceAssessor,
    ) -> None:
        self._assessor = assessor

    def evaluate(
        self,
        candidate: SourceFindingCandidate,
        document: SourceDocument,
    ) -> SourceFinding | None:
        assessment = self._assessor.assess(
            candidate,
            document,
        )

        if (
            assessment.decision
            is SignificanceDecision.UNRESOLVED
        ):
            return None

        return SourceFinding(
            statement=candidate.statement,
            materiality=assessment.significance,
            evidence=candidate.evidence,
        )
