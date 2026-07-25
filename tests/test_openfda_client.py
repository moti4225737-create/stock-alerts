from unittest.mock import Mock, patch

import requests

from modules.openfda_client import OpenFDAClient


def test_search_returns_results() -> None:
    client = OpenFDAClient(timeout=15)

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "recalling_firm": "Liquidia Technologies",
                "reason_for_recall": "Example recall reason",
            }
        ]
    }

    with patch(
        "modules.openfda_client.requests.get",
        return_value=mock_response,
    ) as mock_get:
        results = client.search_drug_enforcement(
            'recalling_firm:"Liquidia"',
            limit=5,
        )

    assert len(results) == 1
    assert results[0]["recalling_firm"] == "Liquidia Technologies"

    mock_get.assert_called_once_with(
        "https://api.fda.gov/drug/enforcement.json",
        params={
            "search": 'recalling_firm:"Liquidia"',
            "limit": 5,
        },
        timeout=15,
    )

    mock_response.raise_for_status.assert_called_once()


def test_search_includes_api_key() -> None:
    client = OpenFDAClient(
        timeout=20,
        api_key="test-api-key",
    )

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}

    with patch(
        "modules.openfda_client.requests.get",
        return_value=mock_response,
    ) as mock_get:
        client.search_drug_enforcement(
            'recalling_firm:"Liquidia"',
            limit=10,
        )

    mock_get.assert_called_once_with(
        "https://api.fda.gov/drug/enforcement.json",
        params={
            "search": 'recalling_firm:"Liquidia"',
            "limit": 10,
            "api_key": "test-api-key",
        },
        timeout=20,
    )


def test_search_returns_empty_list_for_empty_query() -> None:
    client = OpenFDAClient()

    with patch(
        "modules.openfda_client.requests.get"
    ) as mock_get:
        results = client.search_drug_enforcement("   ")

    assert results == []
    mock_get.assert_not_called()


def test_search_rejects_invalid_limit() -> None:
    client = OpenFDAClient()

    try:
        client.search_drug_enforcement(
            'recalling_firm:"Liquidia"',
            limit=0,
        )
    except ValueError as error:
        assert str(error) == "limit must be at least 1"
    else:
        raise AssertionError(
            "Expected ValueError for limit below 1."
        )


def test_search_returns_empty_list_for_404() -> None:
    client = OpenFDAClient()

    mock_response = Mock()
    mock_response.status_code = 404

    with patch(
        "modules.openfda_client.requests.get",
        return_value=mock_response,
    ):
        results = client.search_drug_enforcement(
            'recalling_firm:"Unknown Company"'
        )

    assert results == []
    mock_response.raise_for_status.assert_not_called()


def test_search_filters_invalid_results() -> None:
    client = OpenFDAClient()

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"recalling_firm": "Liquidia"},
            "invalid result",
            None,
            123,
        ]
    }

    with patch(
        "modules.openfda_client.requests.get",
        return_value=mock_response,
    ):
        results = client.search_drug_enforcement(
            'recalling_firm:"Liquidia"'
        )

    assert results == [
        {"recalling_firm": "Liquidia"}
    ]


def test_search_rejects_non_dictionary_payload() -> None:
    client = OpenFDAClient()

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

    with patch(
        "modules.openfda_client.requests.get",
        return_value=mock_response,
    ):
        try:
            client.search_drug_enforcement(
                'recalling_firm:"Liquidia"'
            )
        except ValueError as error:
            assert (
                str(error)
                == "openFDA returned an unexpected response format."
            )
        else:
            raise AssertionError(
                "Expected ValueError for invalid payload."
            )


def test_search_rejects_non_list_results() -> None:
    client = OpenFDAClient()

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": {
            "recalling_firm": "Liquidia"
        }
    }

    with patch(
        "modules.openfda_client.requests.get",
        return_value=mock_response,
    ):
        try:
            client.search_drug_enforcement(
                'recalling_firm:"Liquidia"'
            )
        except ValueError as error:
            assert (
                str(error)
                == "openFDA results field is not a list."
            )
        else:
            raise AssertionError(
                "Expected ValueError for invalid results field."
            )


def test_search_propagates_request_error() -> None:
    client = OpenFDAClient()

    with patch(
        "modules.openfda_client.requests.get",
        side_effect=requests.RequestException(
            "Network failure"
        ),
    ):
        try:
            client.search_drug_enforcement(
                'recalling_firm:"Liquidia"'
            )
        except requests.RequestException as error:
            assert str(error) == "Network failure"
        else:
            raise AssertionError(
                "Expected requests.RequestException."
            )


if __name__ == "__main__":
    test_search_returns_results()
    test_search_includes_api_key()
    test_search_returns_empty_list_for_empty_query()
    test_search_rejects_invalid_limit()
    test_search_returns_empty_list_for_404()
    test_search_filters_invalid_results()
    test_search_rejects_non_dictionary_payload()
    test_search_rejects_non_list_results()
    test_search_propagates_request_error()

    print("OpenFDAClient tests passed.")