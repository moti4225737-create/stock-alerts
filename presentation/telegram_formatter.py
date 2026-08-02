from models.investor_brief import InvestorBrief


class TelegramFormatter:
    def format(self, brief: InvestorBrief) -> str:
        portfolio_impact = (
            "המניה נמצאת בתיק שלך."
            if brief.portfolio_impact.matches_portfolio
            else "לא נמצאה התאמה ישירה לתיק."
        )

        action_consideration = (
            "יש לעיין במקור הרשמי ולהעריך האם נדרשת פעולה."
        )

        return (
            f"דחיפות: {brief.event.importance}/10\n\n"
            f"{brief.event.symbol}\n"
            f"{brief.headline}\n\n"
            f"מה קרה:\n"
            f"{brief.summary}\n\n"
            f"למה זה חשוב:\n"
            f"{brief.explanation.why_it_matters}\n\n"
            f"השפעה על התיק:\n"
            f"{portfolio_impact}\n\n"
            f"הקשר שוק:\n"
            f"{brief.explanation.market_context}\n\n"
            f"מה לשקול:\n"
            f"{action_consideration}\n\n"
            f"מקור: {brief.event.source}\n"
            f"{brief.event.url}"
        )