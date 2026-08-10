import pytest

from models.event import Event
from models.intelligence_story import (
    IntelligenceStory,
    StoryTransitionKind,
)
from models.intelligence_timeline import IntelligenceTimeline


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


def test_story_preserves_timeline_and_current_transition() -> None:
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

    story = IntelligenceStory(
        story_key="cyberhawk-acquisition",
        title="Cyberhawk acquisition",
        timeline=timeline,
        current_transition=StoryTransitionKind.COMPLETION,
    )

    assert story.story_key == "cyberhawk-acquisition"
    assert story.title == "Cyberhawk acquisition"
    assert story.symbol == "ONDS"
    assert story.timeline.events == (
        announced,
        completed,
    )
    assert story.previous_event is announced
    assert story.current_event is completed
    assert (
        story.current_transition
        is StoryTransitionKind.COMPLETION
    )


def test_story_supports_single_event_as_new_story() -> None:
    event = make_event(
        title="New material event",
        published_at="2026-08-10",
    )

    story = IntelligenceStory(
        story_key="new-material-event",
        title="New material event",
        timeline=IntelligenceTimeline(
            symbol="ONDS",
            events=(event,),
        ),
        current_transition=StoryTransitionKind.NEW,
    )

    assert story.previous_event is None
    assert story.current_event is event
    assert story.current_transition is StoryTransitionKind.NEW


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
    ],
)
def test_story_rejects_blank_identity(
    value: str,
) -> None:
    event = make_event(
        title="Event",
        published_at="2026-08-10",
    )

    timeline = IntelligenceTimeline(
        symbol="ONDS",
        events=(event,),
    )

    with pytest.raises(ValueError):
        IntelligenceStory(
            story_key=value,
            title="Story",
            timeline=timeline,
            current_transition=StoryTransitionKind.NEW,
        )


def test_story_rejects_empty_timeline() -> None:
    with pytest.raises(ValueError):
        IntelligenceStory(
            story_key="empty-story",
            title="Empty story",
            timeline=IntelligenceTimeline(
                symbol="ONDS",
            ),
            current_transition=StoryTransitionKind.NEW,
        )
