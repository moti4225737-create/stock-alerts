import json
from pathlib import Path

from models.event import Event
from models.intelligence_story import (
    IntelligenceStory,
    StoryTransitionKind,
)
from models.intelligence_timeline import IntelligenceTimeline


class FileStoryRepository:
    def __init__(
        self,
        path: Path | str,
    ) -> None:
        self._path = Path(path)

    def save(
        self,
        story: IntelligenceStory,
    ) -> None:
        stories = list(
            self._load_all()
        )

        stories = [
            existing
            for existing in stories
            if existing.story_key != story.story_key
        ]
        stories.append(story)

        self._persist(stories)

    def list_by_symbol(
        self,
        symbol: str,
    ) -> tuple[IntelligenceStory, ...]:
        normalized_symbol = symbol.strip().upper()

        return tuple(
            story
            for story in self._load_all()
            if story.symbol == normalized_symbol
        )

    def _load_all(
        self,
    ) -> tuple[IntelligenceStory, ...]:
        if not self._path.exists():
            return ()

        raw = json.loads(
            self._path.read_text(
                encoding="utf-8",
            )
        )

        return tuple(
            self._deserialize_story(item)
            for item in raw
        )

    def _persist(
        self,
        stories: list[IntelligenceStory],
    ) -> None:
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = [
            self._serialize_story(story)
            for story in stories
        ]

        self._path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _serialize_story(
        story: IntelligenceStory,
    ) -> dict:
        return {
            "story_key": story.story_key,
            "title": story.title,
            "current_transition": (
                story.current_transition.value
            ),
            "symbol": story.symbol,
            "events": [
                {
                    "symbol": event.symbol,
                    "source": event.source,
                    "title": event.title,
                    "summary": event.summary,
                    "published_at": event.published_at,
                    "importance": event.importance,
                    "sentiment": event.sentiment,
                    "url": event.url,
                }
                for event in story.timeline.events
            ],
        }

    @staticmethod
    def _deserialize_story(
        item: dict,
    ) -> IntelligenceStory:
        events = tuple(
            Event(
                symbol=event["symbol"],
                source=event["source"],
                title=event["title"],
                summary=event["summary"],
                published_at=event["published_at"],
                importance=event["importance"],
                sentiment=event["sentiment"],
                url=event.get("url"),
            )
            for event in item["events"]
        )

        return IntelligenceStory(
            story_key=item["story_key"],
            title=item["title"],
            timeline=IntelligenceTimeline(
                symbol=item["symbol"],
                events=events,
            ),
            current_transition=StoryTransitionKind(
                item["current_transition"]
            ),
        )
