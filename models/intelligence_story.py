from dataclasses import dataclass
from enum import Enum

from models.event import Event
from models.intelligence_timeline import IntelligenceTimeline


class StoryTransitionKind(str, Enum):
    NEW = "new"
    CONTINUATION = "continuation"
    CONFIRMATION = "confirmation"
    COMPLETION = "completion"
    REVERSAL = "reversal"
    VALIDATION = "validation"


@dataclass(frozen=True, slots=True)
class IntelligenceStory:
    story_key: str
    title: str
    timeline: IntelligenceTimeline
    current_transition: StoryTransitionKind

    def __post_init__(self) -> None:
        normalized_story_key = self.story_key.strip()
        normalized_title = self.title.strip()

        if not normalized_story_key:
            raise ValueError("story_key must not be empty")

        if not normalized_title:
            raise ValueError("title must not be empty")

        if not self.timeline.events:
            raise ValueError("timeline must contain at least one event")

        object.__setattr__(
            self,
            "story_key",
            normalized_story_key,
        )
        object.__setattr__(
            self,
            "title",
            normalized_title,
        )

    @property
    def symbol(self) -> str:
        return self.timeline.symbol

    @property
    def current_event(self) -> Event:
        return self.timeline.events[-1]

    @property
    def previous_event(self) -> Event | None:
        if len(self.timeline.events) < 2:
            return None

        return self.timeline.events[-2]
