from dataclasses import dataclass

from models.source_document import SourceDocument


@dataclass(frozen=True)
class AIBenchmarkCase:
    document: SourceDocument
    must_find: tuple[str, ...]
    should_find: tuple[str, ...]
    must_not_claim: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.must_find:
            raise ValueError(
                "at least one must_find statement is required"
            )

        groups = (
            self.must_find,
            self.should_find,
            self.must_not_claim,
        )

        for group in groups:
            if any(
                not statement.strip()
                for statement in group
            ):
                raise ValueError(
                    "ground truth statements cannot be blank"
                )
