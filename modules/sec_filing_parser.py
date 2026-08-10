from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    _IGNORED_TAGS = {
        "head",
        "script",
        "style",
        "ix:header",
        "ix:hidden",
        "ix:resources",
    }

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs,
    ) -> None:
        if tag.lower() in self._IGNORED_TAGS:
            self._ignored_depth += 1

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        if (
            tag.lower() in self._IGNORED_TAGS
            and self._ignored_depth > 0
        ):
            self._ignored_depth -= 1

    def handle_data(
        self,
        data: str,
    ) -> None:
        if self._ignored_depth > 0:
            return

        normalized = " ".join(data.split())

        if normalized:
            self._parts.append(normalized)

    def get_text(self) -> str:
        return " ".join(self._parts)


class SECFilingParser:
    def extract_text(
        self,
        document: str,
    ) -> str:
        if not document:
            return ""

        parser = _TextExtractor()
        parser.feed(document)

        return parser.get_text()
