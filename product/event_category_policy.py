from models.event import Event
from models.investor_intelligence_card import EventCategory


class EventCategoryPolicy:
    def classify(self, event: Event) -> EventCategory:
        if event.source.upper() == "SEC" and "8-K" in event.title.upper():
            return EventCategory.MATERIAL_FILING

        return EventCategory.CORPORATE_DISCLOSURE