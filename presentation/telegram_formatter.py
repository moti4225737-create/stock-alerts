from datetime import datetime

from models.investor_intelligence_card import (
    EventCategory,
    ImportanceLevel,
    InvestorIntelligenceCard,
)
from presentation.professional_term_explainer import (
    ProfessionalTermExplainer,
)


class TelegramFormatter:
    _IMPORTANCE_LABELS = {
        ImportanceLevel.MODERATE: "🟡 בינונית",
        ImportanceLevel.HIGH: "🟠 גבוהה",
        ImportanceLevel.CRITICAL: "🔴 קריטית",
    }

    _EVENT_CATEGORY_LABELS = {
        EventCategory.MATERIAL_FILING: "דיווח מהותי",
        EventCategory.CORPORATE_DISCLOSURE: "דיווח תאגידי",
    }

    def __init__(
        self,
        term_explainer: ProfessionalTermExplainer | None = None,
    ) -> None:
        self._term_explainer = (
            term_explainer or ProfessionalTermExplainer()
        )

    @staticmethod
    def _format_published_at(value: str) -> str:
        if not value:
            return "לא ידוע"

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            formatted = parsed.strftime("%d/%m/%Y %H:%M")

            if parsed.tzinfo is not None:
                offset = parsed.strftime("%z")
                if offset == "+0000":
                    return f"{formatted} UTC"

            return formatted
        except ValueError:
            return value

    def format(self, card: InvestorIntelligenceCard) -> str:
        importance_label = self._IMPORTANCE_LABELS[
            card.importance_level
        ]
        event_category_label = self._EVENT_CATEGORY_LABELS[
            card.event_category
        ]
        professional_title = self._term_explainer.explain(card.title)

        points = tuple(
            point.strip()
            for point in card.points_to_watch
            if point.strip()
        )
        points_to_watch = "\n".join(
            f"• {point}" for point in points[:3]
        )

        sections = [
            f"🧬 {card.symbol}",
            "",
            importance_label,
            f"📌 אירוע: {event_category_label}",
            professional_title,
            "",
            "──────────────────",
            "",
            "📰 מה קרה?",
            card.summary.strip(),
            "",
            "💡 למה זה חשוב?",
            card.why_it_matters.strip(),
            "",
            "🔎 מה ההקשר להערכת האירוע?",
            card.market_context.strip(),
            "",
            "📈 ההשפעה על התיק שלך",
            card.portfolio_impact.strip(),
        ]

        if points_to_watch:
            sections.extend(
                [
                    "",
                    "👀 מה כדאי לעקוב?",
                    points_to_watch,
                ]
            )

        sections.extend(
            [
                "",
                "🕒 פורסם:",
                self._format_published_at(card.published_at),
                "",
                "🔗 מקור:",
                card.source,
            ]
        )

        if card.source_url:
            sections.append(card.source_url)

        return "\n".join(sections)