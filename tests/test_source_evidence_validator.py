from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate
from product.source_evidence_validator import SourceEvidenceValidator


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text=(
            "Revenue increased 18%. "
            "The pivotal milestone is expected in Q2 2027."
        ),
    )


def test_validator_accepts_candidate_grounded_in_source_document() -> None:
    document = make_document()

    candidate = SourceFindingCandidate(
        statement="Revenue increased 18%.",
        evidence=(
            SourceEvidence(
                source_url=document.source_url,
                text="Revenue increased 18%",
            ),
        ),
    )

    validator = SourceEvidenceValidator()

    assert validator.is_valid(
        document=document,
        finding=candidate,
    )


def test_validator_rejects_evidence_not_present_in_document() -> None:
    document = make_document()

    candidate = SourceFindingCandidate(
        statement="Revenue increased 40%.",
        evidence=(
            SourceEvidence(
                source_url=document.source_url,
                text="Revenue increased 40%",
            ),
        ),
    )

    validator = SourceEvidenceValidator()

    assert not validator.is_valid(
        document=document,
        finding=candidate,
    )


def test_validator_rejects_evidence_from_different_source() -> None:
    document = make_document()

    candidate = SourceFindingCandidate(
        statement="Revenue increased 18%.",
        evidence=(
            SourceEvidence(
                source_url="https://example.com/secondary-source",
                text="Revenue increased 18%",
            ),
        ),
    )

    validator = SourceEvidenceValidator()

    assert not validator.is_valid(
        document=document,
        finding=candidate,
    )
