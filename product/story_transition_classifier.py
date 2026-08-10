from models.intelligence_story import StoryTransitionKind
from models.intelligence_timeline import IntelligenceTimeline


class StoryTransitionClassifier:
    _COMPLETION_TERMS = (
        "completed",
        "completion",
        "closed",
        "closing completed",
        "acquisition completed",
        "transaction completed",
    )

    def classify(
        self,
        timeline: IntelligenceTimeline,
    ) -> StoryTransitionKind:
        events = timeline.events

        if len(events) == 1:
            return StoryTransitionKind.NEW

        current_event = events[-1]

        current_text = " ".join(
            (
                current_event.title or "",
                current_event.summary or "",
            )
        ).lower()

        if any(
            term in current_text
            for term in self._COMPLETION_TERMS
        ):
            return StoryTransitionKind.COMPLETION

        return StoryTransitionKind.CONTINUATION
