import pytest

from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate


def test_candidate_requires_grounding_evidence() -> None:
    evidence = SourceEvidence(
        source_url="https://www.sec.gov/example",
        text="The pivotal milestone is expected in Q2 2027.",
        locator="Item 2",
    )

    candidate = SourceFindingCandidate(
        statement="The pivotal milestone is expected in Q2 2027.",
        evidence=(evidence,),
    )

    assert candidate.statement == (
        "The pivotal milestone is expected in Q2 2027."
    )
    assert candidate.evidence == (evidence,)


def test_candidate_rejects_missing_evidence() -> None:
    with pytest.raises(ValueError):
        SourceFindingCandidate(
            statement="Unsupported claim",
            evidence=(),
        )


def test_candidate_rejects_blank_statement() -> None:
    evidence = SourceEvidence(
        source_url="https://www.sec.gov/example",
        text="Evidence",
    )

    with pytest.raises(ValueError):
        SourceFindingCandidate(
            statement="",
            evidence=(evidence,),
        )
