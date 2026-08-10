import pytest

from models.source_evidence import SourceEvidence
from models.source_finding import SourceFinding


def test_source_finding_requires_grounding_evidence() -> None:
    evidence = SourceEvidence(
        source_url="https://www.sec.gov/example",
        text="The company expects the milestone in Q2 2027.",
    )

    finding = SourceFinding(
        statement="The milestone is expected in Q2 2027.",
        materiality=9,
        evidence=(evidence,),
    )

    assert finding.statement == (
        "The milestone is expected in Q2 2027."
    )
    assert finding.materiality == 9
    assert finding.evidence == (evidence,)


def test_source_finding_rejects_missing_evidence() -> None:
    with pytest.raises(ValueError):
        SourceFinding(
            statement="Unsupported claim",
            materiality=8,
            evidence=(),
        )


def test_source_finding_rejects_invalid_materiality() -> None:
    evidence = SourceEvidence(
        source_url="https://www.sec.gov/example",
        text="Evidence",
    )

    with pytest.raises(ValueError):
        SourceFinding(
            statement="Claim",
            materiality=11,
            evidence=(evidence,),
        )
