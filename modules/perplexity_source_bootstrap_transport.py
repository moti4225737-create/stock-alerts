from collections.abc import Callable

from application.source_bootstrap_researcher import GroundedResearchContext
from modules.perplexity_api_request_client import PerplexityAPIRequestError


class PerplexityResearchError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        category: str,
        response_received: bool,
        status_code: int | None,
    ) -> None:
        super().__init__(message)
        self._category = category
        self._response_received = response_received
        self._status_code = status_code

    @property
    def category(self) -> str:
        return self._category

    @property
    def response_received(self) -> bool:
        return self._response_received

    @property
    def status_code(self) -> int | None:
        return self._status_code


class PerplexitySourceBootstrapTransport:
    def __init__(
        self,
        *,
        provider_request: Callable[[GroundedResearchContext], object],
    ) -> None:
        self._provider_request = provider_request

    def __call__(self, context: GroundedResearchContext) -> object:
        try:
            return self._provider_request(context)
        except PerplexityAPIRequestError as exc:
            raise PerplexityResearchError(
                "Perplexity research request failed",
                category=exc.category or "NETWORK_ERROR",
                response_received=bool(exc.response_received),
                status_code=exc.status_code,
            ) from exc
        except OSError as exc:
            raise PerplexityResearchError(
                "Perplexity research request failed",
                category="NETWORK_ERROR",
                response_received=False,
                status_code=None,
            ) from exc
