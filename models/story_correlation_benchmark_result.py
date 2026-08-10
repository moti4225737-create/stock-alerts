from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoryCorrelationBenchmarkResult:
    case_name: str
    expected_is_correlated: bool
    actual_is_correlated: bool
    confidence: float
    reason: str

    @property
    def passed(self) -> bool:
        return (
            self.expected_is_correlated
            == self.actual_is_correlated
        )
