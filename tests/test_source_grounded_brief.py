import pytest

from models.source_evidence import SourceEvidence
from models.source_finding import SourceFinding
from models.source_grounded_brief import SourceGroundedBrief


def make_finding(
    statement: str,
    materiality: int,
) -> SourceFinding:
    return SourceFinding(
        statement=statement,
        materiality=materiality,
        evidence=(
            SourceEvidence(
                source_url="https://www.sec.gov/example",
                text=f"Evidence for {statement}",
                locator="Item 2 — Management's Discussion",
            ),
        ),
    )


def test_source_grounded_brief_preserves_ranked_findings() -> None:
    findings = (
        make_finding("Highest priority", 10),
        make_finding("Medium priority", 7),
        make_finding("Lower priority", 5),
    )

    brief = SourceGroundedBrief(
        findings=findings,
    )

    assert brief.findings == findings


def test_source_grounded_brief_rejects_empty_findings() -> None:
    with pytest.raises(ValueError):
        SourceGroundedBrief(findings=())


def test_source_evidence_preserves_source_locator() -> None:
    evidence = SourceEvidence(
        source_url="https://www.sec.gov/example",
        text="The company expects the milestone in Q2 2027.",
        locator="Item 1 — Business",
    )

    assert evidence.locator == "Item 1 — Business"
