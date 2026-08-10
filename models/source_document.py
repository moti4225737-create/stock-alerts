from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDocument:
    source: str
    source_url: str
    title: str
    text: str

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source is required")

        if not self.source_url.strip():
            raise ValueError("source_url is required")

        if not self.text.strip():
            raise ValueError("text is required")
