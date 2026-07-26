from unittest.mock import Mock, patch

import requests

from modules.clinical_trials_client import ClinicalTrialsClient


def test_search_returns_studies() -> None:
    client = ClinicalTrialsClient(timeout=15)

    mock_response = Mock()
    mock_response.json.return_value = {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT03884465",
                        "briefTitle": "Example Liquidia Study",
                    }
                }
            }
        ]
    }

    with patch(
        "modules.clinical_trials_client.requests.get",
        return_value=mock_response,
    ) as mock_get:
        studies = client.search_studies(
            query="Liquidia Technologies",
            page_size=5,
        )

    assert len(studies) == 1

    identification_module = (
        studies[0]
        .get("protocolSection", {})
        .get("identificationModule", {})
    )

    assert identification_module["nctId"] == "NCT03884465"

    mock_get.assert_called_once_with(
        "https://clinicaltrials.gov/api/v2/studies",
        params={
            "query.term": "Liquidia Technologies",
            "pageSize": 5,
            "format": "json",
        },
        timeout=15,
    )

    mock_response.raise_for_status.assert_called_once()


def test_search_includes_page_token() -> None:
    client = ClinicalTrialsClient(timeout=20)

    mock_response = Mock()
    mock_response.json.return_value = {
        "studies": []
    }

    with patch(
        "modules.clinical_trials_client.requests.get",
        return_value=mock_response,
    ) as mock_get:
        studies = client.search_studies(
            query="Liquidia",
            page_size=10,
            page_token="test-page-token",
        )

    assert studies == []

    mock_get.assert_called_once_with(
        "https://clinicaltrials.gov/api/v2/studies",
        params={
            "query.term": "Liquidia",
            "pageSize": 10,
            "format": "json",
            "pageToken": "test-page-token",
        },
        timeout=20,
    )


def test_search_returns_empty_list_for_empty_query() -> None:
    client = ClinicalTrialsClient()

    with patch(
        "modules.clinical_trials_client.requests.get"
    ) as mock_get:
        studies = client.search_studies("   ")

    assert studies == []
    mock_get.assert_not_called()


def test_search_rejects_non_list_studies() -> None:
    client = ClinicalTrialsClient()

    mock_response = Mock()
    mock_response.json.return_value = {
        "studies": {
            "nctId": "NCT03884465"
        }
    }

    with patch(
        "modules.clinical_trials_client.requests.get",
        return_value=mock_response,
    ):
        try:
            client.search_studies("Liquidia")
        except ValueError as error:
            assert str(error) == "Invalid ClinicalTrials response."
        else:
            raise AssertionError(
                "Expected ValueError for invalid studies field."
            )


def test_search_propagates_request_error() -> None:
    client = ClinicalTrialsClient()

    with patch(
        "modules.clinical_trials_client.requests.get",
        side_effect=requests.RequestException(
            "Network failure"
        ),
    ):
        try:
            client.search_studies("Liquidia")
        except requests.RequestException as error:
            assert str(error) == "Network failure"
        else:
            raise AssertionError(
                "Expected requests.RequestException."
            )


if __name__ == "__main__":
    test_search_returns_studies()
    test_search_includes_page_token()
    test_search_returns_empty_list_for_empty_query()
    test_search_rejects_non_list_studies()
    test_search_propagates_request_error()

    print("ClinicalTrialsClient tests passed.")