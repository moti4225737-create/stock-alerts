from typing import Any

import requests


class OpenFDAClient:
    """
    Small HTTP client for the official openFDA API.

    This client is responsible only for:
    - building openFDA requests
    - sending HTTP requests
    - validating the JSON response
    - returning raw result dictionaries

    Converting those dictionaries into Event objects belongs
    to FDAProvider.
    """

    BASE_URL = "https://api.fda.gov"

    def __init__(
        self,
        timeout: int = 20,
        api_key: str | None = None,
    ) -> None:
        self.timeout = timeout
        self.api_key = api_key

    def search_drug_enforcement(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search the openFDA drug enforcement endpoint.

        Args:
            query:
                Complete openFDA search expression.

                Example:
                    recalling_firm:"Liquidia"

            limit:
                Maximum number of records to request.

        Returns:
            List of raw openFDA result dictionaries.

            An empty list is returned when openFDA reports that
            no matching records were found.
        """
        cleaned_query = query.strip()

        if not cleaned_query:
            return []

        if limit < 1:
            raise ValueError("limit must be at least 1")

        url = f"{self.BASE_URL}/drug/enforcement.json"

        params: dict[str, str | int] = {
            "search": cleaned_query,
            "limit": limit,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        response = requests.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        if response.status_code == 404:
            return []

        response.raise_for_status()

        payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError(
                "openFDA returned an unexpected response format."
            )

        results = payload.get("results", [])

        if not isinstance(results, list):
            raise ValueError(
                "openFDA results field is not a list."
            )

        valid_results: list[dict[str, Any]] = []

        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)

        return valid_results