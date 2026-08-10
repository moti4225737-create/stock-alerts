from dataclasses import dataclass

from models.source_evidence import SourceEvidence


@dataclass(frozen=True)
class SourceFinding:
    statement: str
    materiality: int
    evidence: tuple[SourceEvidence, ...]

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("statement is required")

        if not 1 <= self.materiality <= 10:
            raise ValueError("materiality must be between 1 and 10")

        if not self.evidence:
            raise ValueError("evidence is required")
