import pytest

from models.ai_benchmark_result import AIBenchmarkResult
from models.semantic_finding_proposal import SemanticFindingProposal


def make_proposal() -> SemanticFindingProposal:
    return SemanticFindingProposal(
        statement="The pivotal milestone was delayed.",
        evidence_text="The pivotal milestone was delayed.",
        locator="Item 2",
    )


def test_benchmark_result_preserves_raw_model_output() -> None:
    proposal = make_proposal()

    result = AIBenchmarkResult(
        provider="example-provider",
        model="example-model",
        proposals=(proposal,),
        latency_seconds=12.5,
        input_tokens=125000,
        output_tokens=420,
    )

    assert result.provider == "example-provider"
    assert result.model == "example-model"
    assert result.proposals == (proposal,)
    assert result.latency_seconds == 12.5
    assert result.input_tokens == 125000
    assert result.output_tokens == 420


def test_benchmark_result_allows_no_findings() -> None:
    result = AIBenchmarkResult(
        provider="example-provider",
        model="example-model",
        proposals=(),
        latency_seconds=4.2,
        input_tokens=1000,
        output_tokens=0,
    )

    assert result.proposals == ()


@pytest.mark.parametrize(
    "field,value",
    [
        ("provider", ""),
        ("model", ""),
    ],
)
def test_benchmark_result_rejects_missing_identity(
    field,
    value,
) -> None:
    values = {
        "provider": "example-provider",
        "model": "example-model",
        "proposals": (),
        "latency_seconds": 1.0,
        "input_tokens": 100,
        "output_tokens": 10,
    }
    values[field] = value

    with pytest.raises(ValueError):
        AIBenchmarkResult(**values)


def test_benchmark_result_rejects_negative_latency() -> None:
    with pytest.raises(ValueError):
        AIBenchmarkResult(
            provider="example-provider",
            model="example-model",
            proposals=(),
            latency_seconds=-1.0,
            input_tokens=100,
            output_tokens=10,
        )


@pytest.mark.parametrize(
    "field",
    [
        "input_tokens",
        "output_tokens",
    ],
)
def test_benchmark_result_rejects_negative_token_usage(
    field,
) -> None:
    values = {
        "provider": "example-provider",
        "model": "example-model",
        "proposals": (),
        "latency_seconds": 1.0,
        "input_tokens": 100,
        "output_tokens": 10,
    }
    values[field] = -1

    with pytest.raises(ValueError):
        AIBenchmarkResult(**values)
