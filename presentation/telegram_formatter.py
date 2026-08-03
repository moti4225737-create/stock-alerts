from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)


class TelegramFormatter:
    _IMPORTANCE_LABELS = {
        ImportanceLevel.MODERATE: "בינונית",
        ImportanceLevel.HIGH: "גבוהה",
        ImportanceLevel.CRITICAL: "קריטית",
    }

    _EVENT_CATEGORY_LABELS = {
        EventCategory.MATERIAL_FILING: "דיווח מהותי חדש",
        EventCategory.CORPORATE_DISCLOSURE: "דיווח תאגידי",
    }

    def format(self, card: InvestorIntelligenceCard) -> str:
        importance_label = self._IMPORTANCE_LABELS[card.importance_level]
        event_category_label = self._EVENT_CATEGORY_LABELS[
            card.event_category
        ]

        points_to_watch = "\n".join(
            f"• {point}" for point in card.points_to_watch
        )

        source_lines = [f"מקור: {card.source}"]

        if card.source_url:
            source_lines.append(card.source_url)

        return (
            f"חשיבות: {importance_label}\n"
            f"סוג אירוע: {event_category_label}\n\n"
            f"{card.symbol}\n"
            f"{card.title}\n\n"
            f"מה קרה:\n"
            f"{card.summary}\n\n"
            f"למה זה חשוב:\n"
            f"{card.why_it_matters}\n\n"
            f"השפעה על התיק:\n"
            f"{card.portfolio_impact}\n\n"
            f"נקודות לתשומת לב:\n"
            f"{points_to_watch}\n\n"
            f"{'\n'.join(source_lines)}"
        )