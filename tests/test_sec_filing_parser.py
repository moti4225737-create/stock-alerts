from modules.sec_filing_parser import SECFilingParser


def test_extract_text_removes_html_tags_and_normalizes_whitespace() -> None:
    parser = SECFilingParser()

    text = parser.extract_text(
        """
        <html>
            <body>
                <h1>Quarterly Results</h1>
                <p>Revenue increased by 18%.</p>
                <p>Cash balance was $412 million.</p>
            </body>
        </html>
        """
    )

    assert text == (
        "Quarterly Results "
        "Revenue increased by 18%. "
        "Cash balance was $412 million."
    )


def test_extract_text_returns_empty_for_empty_document() -> None:
    parser = SECFilingParser()

    assert parser.extract_text("") == ""
