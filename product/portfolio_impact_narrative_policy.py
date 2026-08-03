from models.portfolio_impact import PortfolioImpact


class PortfolioImpactNarrativePolicy:
    def describe(self, impact: PortfolioImpact) -> str:
        if impact.matches_portfolio:
            return (
                f"{impact.holding.symbol} מוחזקת בתיק "
                "ולכן האירוע רלוונטי ישירות."
            )

        return "לא נמצאה השפעה ישירה על אחת ההחזקות בתיק."