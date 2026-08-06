from unittest.mock import Mock

from modules.sec_filing_extractor import SECFilingExtractor


def test_extract_fetches_and_parses_filing_document() -> None:
    client = Mock()
    parser = Mock()

    client.fetch_document.return_value = (
        "<html><body>Quarterly results</body></html>"
    )
    parser.extract_text.return_value = "Quarterly results"

    extractor = SECFilingExtractor(
        client=client,
        parser=parser,
    )

    text = extractor.extract(
        "https://www.sec.gov/Archives/example.htm"
    )

    assert text == "Quarterly results"
    client.fetch_document.assert_called_once_with(
        "https://www.sec.gov/Archives/example.htm"
    )
    parser.extract_text.assert_called_once_with(
        "<html><body>Quarterly results</body></html>"
    )


def test_extract_returns_empty_without_url() -> None:
    client = Mock()
    parser = Mock()

    extractor = SECFilingExtractor(
        client=client,
        parser=parser,
    )

    assert extractor.extract(None) == ""
    client.fetch_document.assert_not_called()
    parser.extract_text.assert_not_called()
