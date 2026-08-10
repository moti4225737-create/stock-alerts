from dataclasses import dataclass

from models.semantic_finding_proposal import SemanticFindingProposal


@dataclass(frozen=True)
class AIBenchmarkResult:
    provider: str
    model: str
    proposals: tuple[SemanticFindingProposal, ...]
    latency_seconds: float
    input_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider is required")

        if not self.model.strip():
            raise ValueError("model is required")

        if self.latency_seconds < 0:
            raise ValueError("latency_seconds cannot be negative")

        if self.input_tokens < 0:
            raise ValueError("input_tokens cannot be negative")

        if self.output_tokens < 0:
            raise ValueError("output_tokens cannot be negative")
