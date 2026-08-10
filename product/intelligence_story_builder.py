from typing import Protocol

from models.intelligence_story import (
    IntelligenceStory,
    StoryTransitionKind,
)
from models.intelligence_timeline import IntelligenceTimeline


class StoryTransitionClassifierProtocol(Protocol):
    def classify(
        self,
        timeline: IntelligenceTimeline,
    ) -> StoryTransitionKind:
        ...


class IntelligenceStoryBuilder:
    def __init__(
        self,
        transition_classifier: StoryTransitionClassifierProtocol,
    ) -> None:
        self._transition_classifier = transition_classifier

    def build(
        self,
        story_key: str,
        title: str,
        timeline: IntelligenceTimeline,
    ) -> IntelligenceStory:
        transition = self._transition_classifier.classify(
            timeline
        )

        return IntelligenceStory(
            story_key=story_key,
            title=title,
            timeline=timeline,
            current_transition=transition,
        )
