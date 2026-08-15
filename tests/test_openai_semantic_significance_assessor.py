from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from models.significance_assessment import (
    SignificanceDecision,
)
from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate
from product.openai_semantic_significance_assessor import (
    OpenAISemanticSignificanceAssessor,
)


def make_candidate() -> SourceFindingCandidate:
    statement = "The pivotal milestone was delayed."

    return SourceFindingCandidate(
        statement=statement,
        evidence=(
            SourceEvidence(
                source_url="https://www.sec.gov/example",
                text=statement,
                locator="Item 2",
            ),
        ),
    )


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="8-K",
        text=(
            "The company disclosed that the pivotal "
            "milestone was delayed."
        ),
    )


def make_response(
    *,
    decision: str,
    significance: int | None,
    confidence: float,
    rationale: str,
):
    parsed = SimpleNamespace(
        decision=decision,
        significance=significance,
        confidence=confidence,
        rationale=rationale,
    )

    content = SimpleNamespace(
        type="output_text",
        parsed=parsed,
    )

    message = SimpleNamespace(
        type="message",
        content=(content,),
    )

    return SimpleNamespace(
        output=(message,),
    )


def test_assessor_returns_structured_assessed_significance() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        decision="assessed",
        significance=9,
        confidence=0.94,
        rationale=(
            "The delay materially changes the timing "
            "of a pivotal company milestone."
        ),
    )

    assessor = OpenAISemanticSignificanceAssessor(
        client=client,
        model="test-model",
    )

    assessment = assessor.assess(
        make_candidate(),
        make_document(),
    )

    assert assessment.decision is SignificanceDecision.ASSESSED
    assert assessment.significance == 9
    assert assessment.confidence == 0.94
    assert (
        assessment.rationale
        == "The delay materially changes the timing "
        "of a pivotal company milestone."
    )


def test_assessor_can_abstain_when_significance_is_unresolved() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        decision="unresolved",
        significance=None,
        confidence=0.91,
        rationale=(
            "The available evidence does not establish "
            "enough context to assess investor significance."
        ),
    )

    assessor = OpenAISemanticSignificanceAssessor(
        client=client,
        model="test-model",
    )

    assessment = assessor.assess(
        make_candidate(),
        make_document(),
    )

    assert assessment.decision is SignificanceDecision.UNRESOLVED
    assert assessment.significance is None
    assert assessment.confidence == 0.91


def test_assessor_rejects_unresolved_with_numeric_significance() -> None:
    client = Mock()

    client.responses.parse.return_value = make_response(
        decision="unresolved",
        significance=7,
        confidence=0.90,
        rationale=(
            "The available evidence is insufficient "
            "for a reliable significance assessment."
        ),
    )

    assessor = OpenAISemanticSignificanceAssessor(
        client=client,
        model="test-model",
    )

    with pytest.raises(ValueError):
        assessor.assess(
            make_candidate(),
            make_document(),
        )
