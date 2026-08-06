from unittest.mock import Mock, patch

from modules.sec_filing_client import SECFilingClient


def test_fetch_document_returns_official_filing_html() -> None:
    client = SECFilingClient(
        user_agent="Stock Sentinel test@example.com",
        timeout=15,
    )
    response = Mock()
    response.text = "<html><body>Quarterly filing</body></html>"

    with patch(
        "modules.sec_filing_client.requests.get",
        return_value=response,
    ) as mock_get:
        document = client.fetch_document(
            "https://www.sec.gov/Archives/example.htm"
        )

    assert document == (
        "<html><body>Quarterly filing</body></html>"
    )
    mock_get.assert_called_once_with(
        "https://www.sec.gov/Archives/example.htm",
        headers={
            "User-Agent": "Stock Sentinel test@example.com",
            "Accept-Encoding": "gzip, deflate",
        },
        timeout=15,
    )
    response.raise_for_status.assert_called_once()


def test_fetch_document_returns_empty_for_missing_url() -> None:
    client = SECFilingClient(
        user_agent="Stock Sentinel test@example.com",
    )

    with patch(
        "modules.sec_filing_client.requests.get"
    ) as mock_get:
        document = client.fetch_document(None)

    assert document == ""
    mock_get.assert_not_called()
