from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticFindingProposal:
    statement: str
    evidence_text: str
    locator: str | None = None

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("statement is required")

        if not self.evidence_text.strip():
            raise ValueError("evidence_text is required")

        if self.locator is not None and not self.locator.strip():
            raise ValueError("locator cannot be blank")
