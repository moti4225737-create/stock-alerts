from typing import Any

import requests


class ClinicalTrialsStudyPage(list[dict[str, Any]]):
    def __init__(
        self,
        studies: list[dict[str, Any]],
        next_page_token: str | None,
    ) -> None:
        super().__init__(studies)
        self.next_page_token = next_page_token


class ClinicalTrialsClient:
    """
    Client for the official ClinicalTrials.gov API v2.
    """

    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def search_studies(
        self,
        query: str | None = None,
        page_size: int = 10,
        page_token: str | None = None,
        query_term: str | None = None,
    ) -> ClinicalTrialsStudyPage:
        """
        Search ClinicalTrials.gov studies by sponsor-related fields.

        Args:
            query:
                Sponsor or collaborator search expression.

            page_size:
                Maximum number of studies to return.

            page_token:
                Pagination token returned by the previous request.

        Returns:
            List of study dictionaries.
        """

        normalized_query = (query_term if query_term is not None else query or "").strip()

        if not normalized_query:
            return ClinicalTrialsStudyPage([], None)

        params: dict[str, Any] = {
            "query.term" if query_term is not None else "query.spons": normalized_query,
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
        next_page_token = payload.get("nextPageToken")

        if not isinstance(studies, list):
            raise ValueError("Invalid ClinicalTrials response.")
        if next_page_token is not None and not isinstance(
            next_page_token,
            str,
        ):
            raise ValueError("Invalid ClinicalTrials response.")

        return ClinicalTrialsStudyPage(studies, next_page_token)
