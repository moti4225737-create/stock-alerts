from models.source_finding import SourceFinding


class SourceFindingSelector:
    def __init__(
        self,
        limit: int = 4,
    ) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        self._limit = limit

    def select(
        self,
        findings: tuple[SourceFinding, ...],
    ) -> tuple[SourceFinding, ...]:
        return tuple(
            sorted(
                findings,
                key=lambda finding: finding.materiality,
                reverse=True,
            )[: self._limit]
        )
