from models.event import Event
from models.intelligence_story import (
    IntelligenceStory,
    StoryTransitionKind,
)
from models.intelligence_timeline import IntelligenceTimeline
from product.intelligence_story_builder import (
    IntelligenceStoryBuilder,
)


class StubClassifier:
    def __init__(
        self,
        transition: StoryTransitionKind,
    ) -> None:
        self.transition = transition
        self.received_timeline = None

    def classify(
        self,
        timeline: IntelligenceTimeline,
    ) -> StoryTransitionKind:
        self.received_timeline = timeline
        return self.transition


def make_event(
    title: str,
    published_at: str,
) -> Event:
    return Event(
        symbol="ONDS",
        source="SEC",
        title=title,
        summary=f"Summary for {title}",
        published_at=published_at,
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


def test_builder_creates_story_from_timeline_and_classifier() -> None:
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
        events=(completed, announced),
    )

    classifier = StubClassifier(
        StoryTransitionKind.COMPLETION
    )

    builder = IntelligenceStoryBuilder(
        transition_classifier=classifier,
    )

    story = builder.build(
        story_key="cyberhawk-acquisition",
        title="Cyberhawk acquisition",
        timeline=timeline,
    )

    assert isinstance(story, IntelligenceStory)
    assert story.story_key == "cyberhawk-acquisition"
    assert story.title == "Cyberhawk acquisition"
    assert story.timeline is timeline
    assert (
        story.current_transition
        is StoryTransitionKind.COMPLETION
    )
    assert classifier.received_timeline is timeline


def test_builder_preserves_chronological_story_state() -> None:
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
        events=(completed, announced),
    )

    builder = IntelligenceStoryBuilder(
        transition_classifier=StubClassifier(
            StoryTransitionKind.COMPLETION
        ),
    )

    story = builder.build(
        story_key="cyberhawk-acquisition",
        title="Cyberhawk acquisition",
        timeline=timeline,
    )

    assert story.previous_event is announced
    assert story.current_event is completed
