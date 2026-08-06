from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        normalized = " ".join(data.split())

        if normalized:
            self._parts.append(normalized)

    def get_text(self) -> str:
        return " ".join(self._parts)


class SECFilingParser:
    def extract_text(self, document: str) -> str:
        if not document:
            return ""

        parser = _TextExtractor()
        parser.feed(document)

        return parser.get_text()
