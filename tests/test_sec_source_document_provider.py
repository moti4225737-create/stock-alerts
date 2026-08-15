from unittest.mock import Mock

from models.event import Event
from product.sec_source_document_provider import (
    SECSourceDocumentProvider,
)


def make_event(
    source: str = "SEC",
    url: str | None = "https://www.sec.gov/example",
) -> Event:
    return Event(
        symbol="LQDA",
        source=source,
        title="SEC Filing: 8-K",
        summary="Basic event summary",
        published_at="2026-08-12",
        importance=8,
        sentiment="neutral",
        url=url,
    )


def test_builds_source_document_from_sec_event() -> None:
    extractor = Mock()
    extractor.extract.return_value = (
        "The company entered into a material agreement."
    )

    provider = SECSourceDocumentProvider(
        filing_extractor=extractor,
    )

    event = make_event()
    document = provider.build(event)

    assert document is not None
    assert document.source == "SEC"
    assert document.source_url == "https://www.sec.gov/example"
    assert document.title == "SEC Filing: 8-K"
    assert (
        document.text
        == "The company entered into a material agreement."
    )

    extractor.extract.assert_called_once_with(
        "https://www.sec.gov/example"
    )


def test_returns_none_for_non_sec_event() -> None:
    extractor = Mock()

    provider = SECSourceDocumentProvider(
        filing_extractor=extractor,
    )

    assert provider.build(
        make_event(source="FDA")
    ) is None

    extractor.extract.assert_not_called()


def test_returns_none_when_sec_event_has_no_url() -> None:
    extractor = Mock()

    provider = SECSourceDocumentProvider(
        filing_extractor=extractor,
    )

    assert provider.build(
        make_event(url=None)
    ) is None

    extractor.extract.assert_not_called()


def test_returns_none_when_extracted_document_is_empty() -> None:
    extractor = Mock()
    extractor.extract.return_value = ""

    provider = SECSourceDocumentProvider(
        filing_extractor=extractor,
    )

    assert provider.build(make_event()) is None
