from typing import Any

import requests


class ClinicalTrialsClient:
    """
    Client for the official ClinicalTrials.gov API v2.
    """

    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def search_studies(
        self,
        query: str,
        page_size: int = 10,
        page_token: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search ClinicalTrials.gov studies.

        Args:
            query:
                Search expression.

            page_size:
                Maximum number of studies to return.

            page_token:
                Pagination token returned by the previous request.

        Returns:
            List of study dictionaries.
        """

        if not query.strip():
            return []

        params: dict[str, Any] = {
            "query.term": query,
            "pageSize": page_size,
            "format": "json",
        }

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()

        studies = payload.get("studies", [])

        if not isinstance(studies, list):
            raise ValueError("Invalid ClinicalTrials response.")

        return studies