import requests


class SECFilingClient:
    def __init__(
        self,
        user_agent: str,
        timeout: int = 20,
    ) -> None:
        normalized_user_agent = user_agent.strip()

        if not normalized_user_agent:
            raise ValueError("SEC user agent is required.")

        self._headers = {
            "User-Agent": normalized_user_agent,
            "Accept-Encoding": "gzip, deflate",
        }
        self._timeout = timeout

    def fetch_document(
        self,
        url: str | None,
    ) -> str:
        if not url:
            return ""

        response = requests.get(
            url,
            headers=self._headers,
            timeout=self._timeout,
        )
        response.raise_for_status()

        return response.text
