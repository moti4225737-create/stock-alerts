from models.event import Event
from models.intelligence_story import (
    IntelligenceStory,
    StoryTransitionKind,
)
from models.intelligence_timeline import IntelligenceTimeline
from modules.story_repository import FileStoryRepository


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


def test_repository_persists_story_across_instances(
    tmp_path,
) -> None:
    path = tmp_path / "stories.json"

    story = IntelligenceStory(
        story_key="onds-cyberhawk-acquisition",
        title="Cyberhawk acquisition",
        timeline=IntelligenceTimeline(
            symbol="ONDS",
            events=(
                make_event(
                    "Acquisition announced",
                    "2026-06-18",
                ),
                make_event(
                    "Acquisition completed",
                    "2026-08-10",
                ),
            ),
        ),
        current_transition=StoryTransitionKind.COMPLETION,
    )

    repository = FileStoryRepository(path)
    repository.save(story)

    reloaded_repository = FileStoryRepository(path)
    stories = reloaded_repository.list_by_symbol("onds")

    assert len(stories) == 1

    restored = stories[0]

    assert restored.story_key == "onds-cyberhawk-acquisition"
    assert restored.title == "Cyberhawk acquisition"
    assert restored.symbol == "ONDS"
    assert (
        restored.current_transition
        is StoryTransitionKind.COMPLETION
    )
    assert len(restored.timeline.events) == 2
    assert (
        restored.previous_event.title
        == "Acquisition announced"
    )
    assert (
        restored.current_event.title
        == "Acquisition completed"
    )
