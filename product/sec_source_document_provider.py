from typing import Protocol

from models.event import Event
from models.source_document import SourceDocument


class FilingExtractor(Protocol):
    def extract(
        self,
        url: str | None,
    ) -> str:
        ...


class SECSourceDocumentProvider:
    def __init__(
        self,
        filing_extractor: FilingExtractor,
    ) -> None:
        self._filing_extractor = filing_extractor

    def build(
        self,
        event: Event,
    ) -> SourceDocument | None:
        if event.source.strip().upper() != "SEC":
            return None

        if not event.url:
            return None

        text = self._filing_extractor.extract(
            event.url
        )

        if not text.strip():
            return None

        return SourceDocument(
            source=event.source,
            source_url=event.url,
            title=event.title,
            text=text,
        )
