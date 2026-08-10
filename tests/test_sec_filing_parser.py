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


def test_extract_text_ignores_non_visible_sec_metadata() -> None:
    parser = SECFilingParser()

    text = parser.extract_text(
        """
        <html>
            <head>
                <title>Technical filing title</title>
                <script>technicalScriptValue</script>
                <style>technicalStyleValue</style>
            </head>
            <body>
                <ix:header>
                    <ix:hidden>
                        <ix:nonNumeric>
                            Hidden XBRL metadata
                        </ix:nonNumeric>
                    </ix:hidden>
                    <ix:resources>
                        http://fasb.org/us-gaap/2025
                        EmployeeStockOptionMember
                    </ix:resources>
                </ix:header>

                <h1>Quarterly Results</h1>
                <p>
                    Product revenue was
                    <ix:nonFraction>$129.9 million</ix:nonFraction>.
                </p>
            </body>
        </html>
        """
    )

    assert "Technical filing title" not in text
    assert "technicalScriptValue" not in text
    assert "technicalStyleValue" not in text
    assert "Hidden XBRL metadata" not in text
    assert "fasb.org" not in text
    assert "EmployeeStockOptionMember" not in text

    assert "Quarterly Results" in text
    assert "Product revenue was" in text
    assert "$129.9 million" in text
