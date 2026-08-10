from types import SimpleNamespace
from unittest.mock import Mock

from models.source_document import SourceDocument
from product.openai_semantic_finding_analyzer import (
    OpenAISemanticFindingAnalyzer,
)


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text="The pivotal milestone was delayed.",
    )


def make_message(
    findings,
):
    parsed = SimpleNamespace(
        findings=findings,
    )

    content = SimpleNamespace(
        type="output_text",
        parsed=parsed,
    )

    return SimpleNamespace(
        type="message",
        content=(content,),
    )


def make_response(
    findings,
    input_tokens: int,
    output_tokens: int,
    include_reasoning: bool = False,
):
    output = []

    if include_reasoning:
        output.append(
            SimpleNamespace(
                type="reasoning",
                content=(),
            )
        )

    output.append(
        make_message(findings)
    )

    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return SimpleNamespace(
        output=tuple(output),
        usage=usage,
    )


def test_analyzer_returns_grounded_proposals_and_usage() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        findings=(
            SimpleNamespace(
                statement="The pivotal milestone was delayed.",
                evidence_text="The pivotal milestone was delayed.",
                locator="Risk Factors",
            ),
        ),
        input_tokens=120000,
        output_tokens=350,
    )

    analyzer = OpenAISemanticFindingAnalyzer(
        client=client,
        model="gpt-5.6-luna",
        max_output_tokens=2000,
    )

    document = make_document()
    result = analyzer.analyze(document)

    assert len(result.proposals) == 1
    assert result.input_tokens == 120000
    assert result.output_tokens == 350

    proposal = result.proposals[0]

    assert proposal.statement == (
        "The pivotal milestone was delayed."
    )
    assert proposal.evidence_text == (
        "The pivotal milestone was delayed."
    )
    assert proposal.locator == "Risk Factors"

    call = client.responses.parse.call_args

    assert call.kwargs["model"] == "gpt-5.6-luna"
    assert call.kwargs["max_output_tokens"] == 2000
    assert call.kwargs["text_format"] is not None
    assert document.text in str(call.kwargs["input"])


def test_analyzer_allows_no_findings() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        findings=(),
        input_tokens=1000,
        output_tokens=20,
    )

    analyzer = OpenAISemanticFindingAnalyzer(
        client=client,
        model="gpt-5.6-luna",
        max_output_tokens=2000,
    )

    result = analyzer.analyze(make_document())

    assert result.proposals == ()
    assert result.input_tokens == 1000
    assert result.output_tokens == 20


def test_analyzer_ignores_reasoning_output_before_message() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        findings=(
            SimpleNamespace(
                statement="The pivotal milestone was delayed.",
                evidence_text="The pivotal milestone was delayed.",
                locator="Risk Factors",
            ),
        ),
        input_tokens=120000,
        output_tokens=350,
        include_reasoning=True,
    )

    analyzer = OpenAISemanticFindingAnalyzer(
        client=client,
        model="gpt-5.6-luna",
        max_output_tokens=6000,
    )

    result = analyzer.analyze(make_document())

    assert len(result.proposals) == 1
    assert result.proposals[0].statement == (
        "The pivotal milestone was delayed."
    )
