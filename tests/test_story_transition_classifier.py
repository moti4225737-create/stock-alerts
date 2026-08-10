from models.event import Event
from models.intelligence_story import StoryTransitionKind
from models.intelligence_timeline import IntelligenceTimeline
from product.story_transition_classifier import (
    StoryTransitionClassifier,
)


def make_event(
    title: str,
    published_at: str,
    summary: str | None = None,
) -> Event:
    return Event(
        symbol="ONDS",
        source="SEC",
        title=title,
        summary=summary or f"Summary for {title}",
        published_at=published_at,
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


def test_classifier_marks_first_event_as_new() -> None:
    event = make_event(
        title="Cyberhawk acquisition announced",
        published_at="2026-06-18",
    )

    timeline = IntelligenceTimeline(
        symbol="ONDS",
        events=(event,),
    )

    classifier = StoryTransitionClassifier()

    assert (
        classifier.classify(timeline)
        is StoryTransitionKind.NEW
    )


def test_classifier_marks_announced_to_completed_as_completion() -> None:
    announced = make_event(
        title="Cyberhawk acquisition announced",
        published_at="2026-06-18",
    )
    completed = make_event(
        title="Cyberhawk acquisition completed",
        published_at="2026-08-10",
    )

    timeline = IntelligenceTimeline(
        symbol="ONDS",
        events=(announced, completed),
    )

    classifier = StoryTransitionClassifier()

    assert (
        classifier.classify(timeline)
        is StoryTransitionKind.COMPLETION
    )


def test_classifier_can_use_summary_to_detect_completion() -> None:
    announced = make_event(
        title="Cyberhawk acquisition announced",
        published_at="2026-06-18",
    )
    closing = make_event(
        title="Ondas files Form 8-K",
        published_at="2026-08-10",
        summary=(
            "The company completed the acquisition "
            "of Cyberhawk Holdings."
        ),
    )

    timeline = IntelligenceTimeline(
        symbol="ONDS",
        events=(announced, closing),
    )

    classifier = StoryTransitionClassifier()

    assert (
        classifier.classify(timeline)
        is StoryTransitionKind.COMPLETION
    )


def test_classifier_marks_unresolved_follow_up_as_continuation() -> None:
    announced = make_event(
        title="Strategic transaction announced",
        published_at="2026-06-18",
    )
    update = make_event(
        title="Strategic transaction update",
        published_at="2026-07-10",
        summary=(
            "The transaction remains subject to "
            "customary closing conditions."
        ),
    )

    timeline = IntelligenceTimeline(
        symbol="ONDS",
        events=(announced, update),
    )

    classifier = StoryTransitionClassifier()

    assert (
        classifier.classify(timeline)
        is StoryTransitionKind.CONTINUATION
    )
