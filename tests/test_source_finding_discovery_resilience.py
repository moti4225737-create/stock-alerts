from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate
from application.source_finding_discovery_service import (
    SourceFindingDiscoveryService,
)
from product.source_evidence_validator import (
    SourceEvidenceValidator,
)


class WorkingDiscoverer:
    def discover(
        self,
        document: SourceDocument,
    ) -> tuple[SourceFindingCandidate, ...]:
        return (
            SourceFindingCandidate(
                statement="Cash and cash equivalents were $120 million.",
                evidence=(
                    SourceEvidence(
                        source_url=document.source_url,
                        text=(
                            "Cash and cash equivalents were "
                            "$120 million."
                        ),
                    ),
                ),
            ),
        )


class FailingDiscoverer:
    def discover(
        self,
        document: SourceDocument,
    ) -> tuple[SourceFindingCandidate, ...]:
        raise RuntimeError("semantic analyzer unavailable")


def test_discovery_preserves_valid_findings_when_one_discoverer_fails() -> None:
    document = SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text=(
            "Cash and cash equivalents were "
            "$120 million."
        ),
    )

    service = SourceFindingDiscoveryService(
        discoverers=(
            WorkingDiscoverer(),
            FailingDiscoverer(),
        ),
        evidence_validator=SourceEvidenceValidator(),
    )

    findings = service.discover(document)

    assert len(findings) == 1
    assert findings[0].statement == (
        "Cash and cash equivalents were $120 million."
    )
