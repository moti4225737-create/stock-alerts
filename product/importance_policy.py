from models.event import Event
from models.investor_intelligence_card import ImportanceLevel


class ImportancePolicy:
    def classify(self, event: Event) -> ImportanceLevel:
        if event.importance >= 9:
            return ImportanceLevel.CRITICAL

        if event.importance >= 7:
            return ImportanceLevel.HIGH

        return ImportanceLevel.MODERATE