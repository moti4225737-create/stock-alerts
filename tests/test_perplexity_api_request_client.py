import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from application.source_bootstrap_researcher import GroundedResearchContext
from models.company_identity import CompanyIdentity
from modules.perplexity_api_request_client import PerplexityAPIRequestClient, PerplexityAPIRequestError


ENDPOINT = "https://api.perplexity.ai/v1/sonar"
FAKE_API_KEY = "pxy-test-secret"


def _context() -> GroundedResearchContext:
    return GroundedResearchContext(
        symbol="ONDS",
        time_zero=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
        known_identity=CompanyIdentity(
            ticker="ONDS", company_name="Ondas Holdings Inc.",
            exchange="NASDAQ", cik="0001646188",
        ),
    )


def _candidate(index: int = 0) -> dict:
    return {
        "fact": f"Opening fact {index}",
        "category": "business",
        "evidence": [{
            "source_url": "https://www.sec.gov/Archives/example",
            "text": "Independent supporting text.", "locator": "Item 1",
        }],
    }


def _research_payload(count: int = 1) -> dict:
    return {"candidates": [_candidate(index) for index in range(count)]}


def _response(payload: dict) -> Mock:
    response = Mock(status_code=200)
    response.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": json.dumps(payload)}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        "citations": ["https://www.sec.gov/Archives/example"],
        "search_results": [],
    }
    return response


def _client(http_request: Mock, *, api_key: str | None = FAKE_API_KEY,
            max_output_tokens: object = 3_000) -> PerplexityAPIRequestClient:
    return PerplexityAPIRequestClient(
        api_key=api_key, http_request=http_request,
        timeout_seconds=12, max_output_tokens=max_output_tokens,
    )


def test_request_uses_verified_identity_only_as_research_context() -> None:
    http_request = Mock(return_value=_response(_research_payload()))
    _client(http_request)(_context())
    request = http_request.call_args.kwargs["json"]
    prompt = "\n".join(message["content"] for message in request["messages"])
    assert all(value in prompt for value in (
        "AUTHORIZED CONTEXT", "known_identity", "ONDS",
        "Ondas Holdings Inc.", "0001646188", "NASDAQ",
    ))
    assert "identity" not in request["response_format"]["json_schema"]["schema"]["properties"]


def test_output_schema_exposes_only_candidates() -> None:
    schema = PerplexityAPIRequestClient._research_schema()
    assert set(schema["properties"]) == {"candidates"}
    assert schema["required"] == ["candidates"]
    assert schema["additionalProperties"] is False


def test_candidate_schema_is_exactly_fact_category_and_evidence() -> None:
    candidate = PerplexityAPIRequestClient._research_schema()["properties"]["candidates"]["items"]
    assert set(candidate["properties"]) == {"fact", "category", "evidence"}
    assert set(candidate["required"]) == {"fact", "category", "evidence"}
    assert candidate["additionalProperties"] is False


def test_candidate_schema_has_maximum_ten_and_no_minimum() -> None:
    candidates = PerplexityAPIRequestClient._research_schema()["properties"]["candidates"]
    assert candidates["maxItems"] == 10
    assert candidates.get("minItems", 0) == 0


def test_zero_candidates_is_a_valid_successful_response() -> None:
    http_request = Mock(return_value=_response(_research_payload(0)))
    assert _client(http_request)(_context())["candidates"] == []
    http_request.assert_called_once()


@pytest.mark.parametrize("legacy_field", (
    "identity", "profile", "relationships", "monitoring_requirements",
    "role", "resolution", "materiality", "material",
))
def test_provider_cannot_return_legacy_authority_fields(legacy_field: str) -> None:
    payload = _research_payload()
    payload[legacy_field] = {}
    with pytest.raises(PerplexityAPIRequestError, match="research response is unusable"):
        _client(Mock(return_value=_response(payload)))(_context())


def test_more_than_ten_candidates_is_rejected() -> None:
    with pytest.raises(PerplexityAPIRequestError, match="research response is unusable"):
        _client(Mock(return_value=_response(_research_payload(11))))(_context())


def test_real_client_makes_one_bounded_structured_sonar_pro_request() -> None:
    payload = _research_payload()
    http_request = Mock(return_value=_response(payload))
    result = _client(http_request)(_context())
    http_request.assert_called_once()
    call = http_request.call_args
    assert call.args == (ENDPOINT,)
    assert call.kwargs["headers"] == {
        "Authorization": f"Bearer {FAKE_API_KEY}", "Content-Type": "application/json",
    }
    assert call.kwargs["timeout"] == 12
    request = call.kwargs["json"]
    assert (request["model"], request["stream"], request["max_tokens"]) == ("sonar-pro", False, 3_000)
    assert request["response_format"]["type"] == "json_schema"
    prompt = "\n".join(message["content"] for message in request["messages"])
    assert "candidate opening facts" in prompt.lower()
    assert "fact, category, and evidence" in prompt.lower()
    assert "not authoritative output" in prompt.lower()
    assert FAKE_API_KEY not in prompt
    assert "quantity" not in prompt and "portfolio" not in prompt.lower()
    assert result["candidates"] == payload["candidates"]
    assert result["_operational_evidence"] == {"usage": _response(payload).json.return_value["usage"]}
    assert result["_provider_metadata"] == {
        "citations": ["https://www.sec.gov/Archives/example"], "search_results": [],
    }
    assert FAKE_API_KEY not in json.dumps(result)


def test_missing_api_key_fails_before_http_request() -> None:
    http_request = Mock()
    with pytest.raises(PerplexityAPIRequestError, match="API key is required") as failure:
        _client(http_request, api_key=None)(_context())
    http_request.assert_not_called()
    assert FAKE_API_KEY not in str(failure.value)


@pytest.mark.parametrize("max_output_tokens", (None, 0, -1, True, 1.5, "3000"))
def test_invalid_max_output_tokens_fails_before_http_request(max_output_tokens: object) -> None:
    http_request = Mock()
    with pytest.raises(PerplexityAPIRequestError, match="positive integer"):
        _client(http_request, max_output_tokens=max_output_tokens)
    http_request.assert_not_called()


def test_max_output_tokens_has_no_constructor_default() -> None:
    with pytest.raises(TypeError):
        PerplexityAPIRequestClient(api_key=FAKE_API_KEY, http_request=Mock(), timeout_seconds=12)


@pytest.mark.parametrize(("response", "error"), (
    (Mock(status_code=503), "API request failed"),
    (Mock(status_code=200, json=Mock(side_effect=ValueError("bad"))), "response is not valid JSON"),
    (Mock(status_code=200, json=Mock(return_value={"choices": []})), "research response is unusable"),
    (_response({}), "research response is unusable"),
))
def test_http_or_response_failure_is_fail_closed_without_retry(response: Mock, error: str) -> None:
    http_request = Mock(return_value=response)
    with pytest.raises(PerplexityAPIRequestError, match=error) as failure:
        _client(http_request)(_context())
    http_request.assert_called_once()
    assert FAKE_API_KEY not in str(failure.value)


def test_timeout_is_fail_closed_without_retry_or_secret_leakage() -> None:
    http_request = Mock(side_effect=OSError("timeout"))
    with pytest.raises(PerplexityAPIRequestError, match="API request failed") as failure:
        _client(http_request)(_context())
    http_request.assert_called_once()
    assert FAKE_API_KEY not in str(failure.value)
