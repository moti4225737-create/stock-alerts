from datetime import datetime

from models.investor_intelligence_card import InvestorIntelligenceCard
from presentation.professional_term_explainer import (
    ProfessionalTermExplainer,
)


class TelegramFormatter:
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
            return "\u05dc\u05d0 \u05d9\u05d3\u05d5\u05e2"

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if (
                parsed.hour == 0
                and parsed.minute == 0
                and parsed.second == 0
            ):
                return parsed.strftime("%d/%m/%Y")

            formatted = parsed.strftime("%d/%m/%Y %H:%M")

            if (
                parsed.tzinfo is not None
                and parsed.strftime("%z") == "+0000"
            ):
                return f"{formatted} UTC"

            return formatted
        except ValueError:
            return value

    def _format_title(
        self,
        card: InvestorIntelligenceCard,
    ) -> str:
        title = self._term_explainer.explain(
            card.title.strip()
        )

        if card.symbol.upper() in title.upper():
            return title

        return f"{card.symbol} \u2014 {title}"

    def format(
        self,
        card: InvestorIntelligenceCard,
    ) -> str:
        sections = [
            self._format_title(card),
            "",
            card.summary.strip(),
            "",
            "\U0001f4a1 \u05dc\u05de\u05d4 \u05d6\u05d4 \u05d7\u05e9\u05d5\u05d1?",
            card.why_it_matters.strip(),
            "",
            "\U0001f552 \u05e4\u05d5\u05e8\u05e1\u05dd:",
            self._format_published_at(card.published_at),
            "",
            "\U0001f517 \u05de\u05e7\u05d5\u05e8:",
            card.source.strip(),
        ]

        if card.source_url:
            sections.append(card.source_url)

        return "\n".join(sections)
