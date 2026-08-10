from dataclasses import dataclass

from models.event import Event


@dataclass(frozen=True, slots=True)
class StoryCorrelationBenchmarkCase:
    name: str
    earlier_event: Event
    current_event: Event
    expected_is_correlated: bool

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name is required")

        earlier_symbol = (
            self.earlier_event.symbol.strip().upper()
        )
        current_symbol = (
            self.current_event.symbol.strip().upper()
        )

        if earlier_symbol != current_symbol:
            raise ValueError(
                "benchmark events must belong "
                "to the same symbol"
            )
