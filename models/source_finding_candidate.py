from dataclasses import dataclass

from models.source_evidence import SourceEvidence


@dataclass(frozen=True)
class SourceFindingCandidate:
    statement: str
    evidence: tuple[SourceEvidence, ...]

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("statement is required")

        if not self.evidence:
            raise ValueError("evidence is required")
