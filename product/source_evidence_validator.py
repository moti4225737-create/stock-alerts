from models.source_document import SourceDocument
from models.source_finding_candidate import SourceFindingCandidate


class SourceEvidenceValidator:
    def is_valid(
        self,
        document: SourceDocument,
        finding: SourceFindingCandidate,
    ) -> bool:
        for evidence in finding.evidence:
            if evidence.source_url != document.source_url:
                return False

            if evidence.text not in document.text:
                return False

        return True
