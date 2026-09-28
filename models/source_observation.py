from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class SourceObservationState:
    schema: str
    version: int
    source: str
    scope: str
    objects: dict[str, dict]
    pending: tuple[dict, ...] = ()
    observed_through: str | None = None
