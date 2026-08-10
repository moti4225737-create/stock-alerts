import pytest

from models.analyzer_execution_result import AnalyzerExecutionResult
from models.semantic_finding_proposal import SemanticFindingProposal


def make_proposal() -> SemanticFindingProposal:
    return SemanticFindingProposal(
        statement="The pivotal milestone was delayed.",
        evidence_text="The pivotal milestone was delayed.",
    )


def test_execution_result_preserves_proposals_and_usage() -> None:
    proposal = make_proposal()

    result = AnalyzerExecutionResult(
        proposals=(proposal,),
        input_tokens=120000,
        output_tokens=350,
    )

    assert result.proposals == (proposal,)
    assert result.input_tokens == 120000
    assert result.output_tokens == 350


@pytest.mark.parametrize(
    "field",
    [
        "input_tokens",
        "output_tokens",
    ],
)
def test_execution_result_rejects_negative_usage(
    field,
) -> None:
    values = {
        "proposals": (),
        "input_tokens": 100,
        "output_tokens": 10,
    }
    values[field] = -1

    with pytest.raises(ValueError):
        AnalyzerExecutionResult(**values)
