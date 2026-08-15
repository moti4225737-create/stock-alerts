import pytest

from models.significance_assessment import (
    SignificanceAssessment,
    SignificanceDecision,
)


def test_significance_assessment_preserves_assessed_dimensions() -> None:
    assessment = SignificanceAssessment(
        decision=SignificanceDecision.ASSESSED,
        significance=9,
        confidence=0.92,
        rationale=(
            "The finding materially changes the expected "
            "timing of a pivotal milestone."
        ),
    )

    assert assessment.decision is SignificanceDecision.ASSESSED
    assert assessment.significance == 9
    assert assessment.confidence == 0.92
    assert assessment.rationale == (
        "The finding materially changes the expected "
        "timing of a pivotal milestone."
    )


@pytest.mark.parametrize(
    "significance",
    (0, 11),
)
def test_assessed_significance_rejects_invalid_numeric_value(
    significance: int,
) -> None:
    with pytest.raises(ValueError):
        SignificanceAssessment(
            decision=SignificanceDecision.ASSESSED,
            significance=significance,
            confidence=0.8,
            rationale="Supported assessment.",
        )


@pytest.mark.parametrize(
    "confidence",
    (-0.01, 1.01),
)
def test_significance_assessment_rejects_invalid_confidence(
    confidence: float,
) -> None:
    with pytest.raises(ValueError):
        SignificanceAssessment(
            decision=SignificanceDecision.ASSESSED,
            significance=8,
            confidence=confidence,
            rationale="Supported assessment.",
        )


def test_significance_assessment_requires_rationale() -> None:
    with pytest.raises(ValueError):
        SignificanceAssessment(
            decision=SignificanceDecision.ASSESSED,
            significance=8,
            confidence=0.9,
            rationale="   ",
        )


def test_significance_assessment_allows_explicit_unresolved_decision() -> None:
    assessment = SignificanceAssessment(
        decision=SignificanceDecision.UNRESOLVED,
        significance=None,
        confidence=0.91,
        rationale=(
            "The evidence does not establish enough "
            "context to assess investor significance."
        ),
    )

    assert assessment.decision is SignificanceDecision.UNRESOLVED
    assert assessment.significance is None
    assert assessment.confidence == 0.91


def test_unresolved_assessment_rejects_numeric_significance() -> None:
    with pytest.raises(ValueError):
        SignificanceAssessment(
            decision=SignificanceDecision.UNRESOLVED,
            significance=5,
            confidence=0.9,
            rationale="Insufficient evidence.",
        )


def test_assessed_decision_requires_numeric_significance() -> None:
    with pytest.raises(ValueError):
        SignificanceAssessment(
            decision=SignificanceDecision.ASSESSED,
            significance=None,
            confidence=0.9,
            rationale="Assessment completed.",
        )


def test_significance_assessment_rejects_non_enum_decision() -> None:
    with pytest.raises(ValueError):
        SignificanceAssessment(
            decision="assessed",
            significance=9,
            confidence=0.9,
            rationale="Supported assessment.",
        )
