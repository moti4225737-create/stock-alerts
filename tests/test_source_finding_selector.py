from models.source_evidence import SourceEvidence
from models.source_finding import SourceFinding
from product.source_finding_selector import SourceFindingSelector


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
            ),
        ),
    )


def test_selector_returns_top_findings_by_materiality() -> None:
    selector = SourceFindingSelector(limit=4)

    findings = (
        make_finding("Finding 6", 6),
        make_finding("Finding 10", 10),
        make_finding("Finding 8", 8),
        make_finding("Finding 5", 5),
        make_finding("Finding 9", 9),
        make_finding("Finding 7", 7),
    )

    selected = selector.select(findings)

    assert [
        finding.materiality
        for finding in selected
    ] == [10, 9, 8, 7]


def test_selector_does_not_mutate_original_findings() -> None:
    selector = SourceFindingSelector(limit=2)

    findings = (
        make_finding("Finding 5", 5),
        make_finding("Finding 9", 9),
        make_finding("Finding 7", 7),
    )

    original = findings

    selector.select(findings)

    assert findings == original
