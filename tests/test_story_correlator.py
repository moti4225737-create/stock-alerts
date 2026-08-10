from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationResult,
)
from product.story_correlator import StoryCorrelator


def make_event(
    title: str,
    summary: str,
    published_at: str,
) -> Event:
    return Event(
        symbol="ONDS",
        source="SEC",
        title=title,
        summary=summary,
        published_at=published_at,
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


def test_correlator_matches_same_acquisition_story() -> None:
    earlier = make_event(
        title="Ondas announces Cyberhawk acquisition",
        summary=(
            "Ondas entered into an agreement to acquire "
            "Cyberhawk Holdings."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        title="Ondas files Form 8-K",
        summary=(
            "Ondas completed the acquisition of "
            "Cyberhawk Holdings."
        ),
        published_at="2026-08-10",
    )

    result = StoryCorrelator().correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert isinstance(result, StoryCorrelationResult)
    assert result.is_correlated
    assert result.confidence == 1.0
    assert result.reason


def test_correlator_rejects_unrelated_event_for_same_symbol() -> None:
    earlier = make_event(
        title="Ondas announces Cyberhawk acquisition",
        summary=(
            "Ondas entered into an agreement to acquire "
            "Cyberhawk Holdings."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        title="Ondas reports quarterly results",
        summary=(
            "Ondas reported second-quarter revenue "
            "and updated guidance."
        ),
        published_at="2026-08-13",
    )

    result = StoryCorrelator().correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert not result.is_correlated
    assert result.confidence == 1.0
    assert result.reason


def test_correlator_matches_subject_from_summary_when_title_is_generic() -> None:
    earlier = make_event(
        title="Strategic transaction announced",
        summary=(
            "The company agreed to acquire "
            "Cyberhawk Holdings."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        title="Form 8-K",
        summary=(
            "The acquisition of Cyberhawk Holdings "
            "was completed."
        ),
        published_at="2026-08-10",
    )

    result = StoryCorrelator().correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert result.is_correlated
    assert result.confidence == 1.0


def test_correlator_returns_uncertain_when_context_is_insufficient() -> None:
    earlier = make_event(
        title="Strategic transaction announced",
        summary="The company announced a transaction.",
        published_at="2026-06-18",
    )

    current = make_event(
        title="Strategic update",
        summary="The company provided an update.",
        published_at="2026-07-10",
    )

    result = StoryCorrelator().correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert not result.is_correlated
    assert result.confidence == 0.5
    assert result.reason
