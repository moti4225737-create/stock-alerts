from dataclasses import dataclass

from models.source_finding import SourceFinding


@dataclass(frozen=True)
class SourceGroundedBrief:
    findings: tuple[SourceFinding, ...]

    def __post_init__(self) -> None:
        if not self.findings:
            raise ValueError("at least one finding is required")
