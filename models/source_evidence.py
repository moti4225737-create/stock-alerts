from dataclasses import dataclass


@dataclass(frozen=True)
class SourceEvidence:
    source_url: str
    text: str
    locator: str | None = None

    def __post_init__(self) -> None:
        if not self.source_url.strip():
            raise ValueError("source_url is required")

        if not self.text.strip():
            raise ValueError("evidence text is required")

        if self.locator is not None and not self.locator.strip():
            raise ValueError("locator cannot be blank")
