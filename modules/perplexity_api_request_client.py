import json
from collections.abc import Callable, Mapping

import requests

from application.source_bootstrap_researcher import GroundedResearchContext


class PerplexityAPIRequestError(OSError):
    def __init__(
        self,
        message: str,
        *,
        category: str | None = None,
        response_received: bool | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self._category = category
        self._response_received = response_received
        self._status_code = status_code

    @property
    def category(self) -> str | None:
        return self._category

    @property
    def response_received(self) -> bool | None:
        return self._response_received

    @property
    def status_code(self) -> int | None:
        return self._status_code


class PerplexityAPIRequestClient:
    ENDPOINT = "https://api.perplexity.ai/v1/sonar"
    MODEL = "sonar-pro"

    def __init__(
        self,
        *,
        api_key: str | None,
        http_request: Callable[..., object],
        timeout_seconds: int | float,
        max_output_tokens: int,
    ) -> None:
        if (
            isinstance(max_output_tokens, bool)
            or not isinstance(max_output_tokens, int)
            or max_output_tokens <= 0
        ):
            raise PerplexityAPIRequestError(
                "max_output_tokens must be a positive integer"
            )
        self._api_key = api_key
        self._http_request = http_request
        self._timeout_seconds = timeout_seconds
        self._max_output_tokens = max_output_tokens

    def __call__(self, context: GroundedResearchContext) -> dict:
        api_key = self._normalized_api_key()
        request_body = self._request_body(context)

        try:
            response = self._http_request(
                self.ENDPOINT,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
                timeout=self._timeout_seconds,
            )
        except requests.exceptions.ConnectTimeout as exc:
            raise PerplexityAPIRequestError(
                "Perplexity API request failed",
                category="CONNECT_TIMEOUT",
                response_received=False,
                status_code=None,
            ) from exc
        except requests.exceptions.ReadTimeout as exc:
            raise PerplexityAPIRequestError(
                "Perplexity API request failed",
                category="READ_TIMEOUT",
                response_received=False,
                status_code=None,
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise PerplexityAPIRequestError(
                "Perplexity API request failed",
                category="TIMEOUT",
                response_received=False,
                status_code=None,
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise PerplexityAPIRequestError(
                "Perplexity API request failed",
                category="NETWORK_ERROR",
                response_received=False,
                status_code=None,
            ) from exc
        except OSError as exc:
            raise PerplexityAPIRequestError(
                "Perplexity API request failed",
                category="NETWORK_ERROR",
                response_received=False,
                status_code=None,
            ) from exc

        response_status = getattr(response, "status_code", None)
        if response_status != 200:
            safe_status = (
                response_status
                if isinstance(response_status, int)
                and not isinstance(response_status, bool)
                else None
            )
            raise PerplexityAPIRequestError(
                "Perplexity API request failed",
                category=(
                    "AUTHENTICATION_AUTHORIZATION"
                    if safe_status in (401, 403)
                    else "HTTP_STATUS"
                ),
                response_received=True,
                status_code=safe_status,
            )

        try:
            response_payload = response.json()
        except (ValueError, TypeError, AttributeError) as exc:
            raise PerplexityAPIRequestError(
                "Perplexity API response is not valid JSON",
                category="PROVIDER_RESPONSE_PARSE",
                response_received=True,
                status_code=200,
            ) from exc

        research = self._research_payload(response_payload)
        result = dict(research)
        result["_operational_evidence"] = {
            "usage": response_payload.get("usage")
        }
        result["_provider_metadata"] = {
            "citations": response_payload.get("citations"),
            "search_results": response_payload.get("search_results"),
        }
        return result

    def _normalized_api_key(self) -> str:
        if not isinstance(self._api_key, str) or not self._api_key.strip():
            raise PerplexityAPIRequestError(
                "Perplexity API key is required",
                category="AUTHENTICATION_AUTHORIZATION",
                response_received=False,
                status_code=None,
            )
        return self._api_key.strip()

    def _request_body(self, context: GroundedResearchContext) -> dict:
        authorized_context: dict[str, object] = {
            "symbol": context.symbol,
            "time_zero": context.time_zero.isoformat(),
        }
        if context.known_identity is not None:
            identity = context.known_identity
            authorized_context["known_identity"] = {
                "ticker": identity.ticker,
                "company_name": identity.company_name,
                "country": identity.country,
                "exchange": identity.exchange,
                "industry": identity.industry,
                "cik": identity.cik,
                "website": identity.website,
            }

        prompt = (
            "Research this single Source Bootstrap context. Return zero to "
            "ten candidate Opening facts. Each candidate must contain only "
            "fact, category, and evidence with provenance. The known identity "
            "is Sentinel-owned research context only and is not authoritative "
            "output: do not return, modify, enrich, or repeat identity. Do not "
            "return profiles, asset relationships, monitoring requirements, "
            "roles, resolutions, materiality, dispositions, readiness, "
            "acceptance, or authority.\n\n"
            f"AUTHORIZED CONTEXT:\n{json.dumps(authorized_context)}"
        )
        return {
            "model": self.MODEL,
            "stream": False,
            "max_tokens": self._max_output_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "schema": self._research_schema(),
                },
            },
        }

    @staticmethod
    def _research_schema() -> dict:
        nullable_string = {"type": ["string", "null"]}
        evidence = {
            "type": "object",
            "properties": {
                "source_url": {"type": "string"},
                "text": {"type": "string"},
                "locator": nullable_string,
            },
            "required": ["source_url", "text", "locator"],
            "additionalProperties": False,
        }
        candidate = {
            "type": "object",
            "properties": {
                "fact": {"type": "string"},
                "category": {"type": "string"},
                "evidence": {"type": "array", "items": evidence},
            },
            "required": ["fact", "category", "evidence"],
            "additionalProperties": False,
        }
        return {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": candidate,
                    "maxItems": 10,
                },
            },
            "required": ["candidates"],
            "additionalProperties": False,
        }

    @classmethod
    def _research_payload(cls, response_payload: object) -> Mapping:
        if not isinstance(response_payload, Mapping):
            raise PerplexityAPIRequestError(
                "Perplexity API research response is unusable",
                category="STRUCTURED_OUTPUT_SCHEMA",
                response_received=True,
                status_code=200,
            )
        try:
            choices = response_payload["choices"]
            content = choices[0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise PerplexityAPIRequestError(
                "Perplexity API research response is unusable",
                category="STRUCTURED_OUTPUT_SCHEMA",
                response_received=True,
                status_code=200,
            ) from exc
        if not isinstance(content, str):
            raise PerplexityAPIRequestError(
                "Perplexity API research response is unusable",
                category="STRUCTURED_OUTPUT_SCHEMA",
                response_received=True,
                status_code=200,
            )
        try:
            research = json.loads(content)
        except (ValueError, TypeError) as exc:
            raise PerplexityAPIRequestError(
                "Perplexity API research response is unusable",
                category="STRUCTURED_OUTPUT_SCHEMA",
                response_received=True,
                status_code=200,
            ) from exc
        if not cls._is_usable_research(research):
            raise PerplexityAPIRequestError(
                "Perplexity API research response is unusable",
                category="STRUCTURED_OUTPUT_SCHEMA",
                response_received=True,
                status_code=200,
            )
        return research

    @staticmethod
    def _is_usable_research(value: object) -> bool:
        if not isinstance(value, Mapping) or set(value) != {"candidates"}:
            return False
        candidates = value.get("candidates")
        if not isinstance(candidates, list) or len(candidates) > 10:
            return False
        for candidate in candidates:
            if not isinstance(candidate, Mapping) or set(candidate) != {
                "fact",
                "category",
                "evidence",
            }:
                return False
            if not isinstance(candidate["fact"], str):
                return False
            if not isinstance(candidate["category"], str):
                return False
            evidence_items = candidate["evidence"]
            if not isinstance(evidence_items, list):
                return False
            for evidence_item in evidence_items:
                if not isinstance(evidence_item, Mapping) or set(
                    evidence_item
                ) != {"source_url", "text", "locator"}:
                    return False
                if not isinstance(evidence_item["source_url"], str):
                    return False
                if not isinstance(evidence_item["text"], str):
                    return False
                if evidence_item["locator"] is not None and not isinstance(
                    evidence_item["locator"], str
                ):
                    return False
        return True
