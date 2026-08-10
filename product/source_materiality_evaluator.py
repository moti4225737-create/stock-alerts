from models.source_finding import SourceFinding
from models.source_finding_candidate import SourceFindingCandidate


class SourceMaterialityEvaluator:
    def __init__(
        self,
        policy: dict[str, int],
        default_materiality: int = 5,
    ) -> None:
        if not 1 <= default_materiality <= 10:
            raise ValueError(
                "default_materiality must be between 1 and 10"
            )

        self._policy = {
            key.lower(): value
            for key, value in policy.items()
        }
        self._default_materiality = default_materiality

    def evaluate(
        self,
        candidate: SourceFindingCandidate,
    ) -> SourceFinding:
        statement = candidate.statement.lower()

        materiality = self._default_materiality

        for keyword, score in self._policy.items():
            if keyword in statement:
                materiality = score
                break

        return SourceFinding(
            statement=candidate.statement,
            materiality=materiality,
            evidence=candidate.evidence,
        )
