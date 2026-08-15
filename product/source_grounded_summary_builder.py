from models.source_grounded_brief import SourceGroundedBrief


class SourceGroundedSummaryBuilder:
    def build(
        self,
        brief: SourceGroundedBrief,
    ) -> str:
        return " ".join(
            finding.statement.strip()
            for finding in brief.findings
            if finding.statement.strip()
        )
