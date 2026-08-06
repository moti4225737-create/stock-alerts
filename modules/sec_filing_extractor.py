from typing import Protocol


class FilingClient(Protocol):
    def fetch_document(
        self,
        url: str | None,
    ) -> str:
        ...


class FilingParser(Protocol):
    def extract_text(
        self,
        document: str,
    ) -> str:
        ...


class SECFilingExtractor:
    def __init__(
        self,
        client: FilingClient,
        parser: FilingParser,
    ) -> None:
        self._client = client
        self._parser = parser

    def extract(
        self,
        url: str | None,
    ) -> str:
        if not url:
            return ""

        document = self._client.fetch_document(url)

        if not document:
            return ""

        return self._parser.extract_text(document)
