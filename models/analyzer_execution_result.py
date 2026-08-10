from dataclasses import dataclass

from models.semantic_finding_proposal import SemanticFindingProposal


@dataclass(frozen=True)
class AnalyzerExecutionResult:
    proposals: tuple[SemanticFindingProposal, ...]
    input_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        if self.input_tokens < 0:
            raise ValueError("input_tokens cannot be negative")

        if self.output_tokens < 0:
            raise ValueError("output_tokens cannot be negative")
