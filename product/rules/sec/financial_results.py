from models.event import Event


class SecFinancialResultsSummaryRule:
    rule_id = "sec.8k.financial_results"
    priority = 300

    _PATTERN = "RESULTS OF OPERATIONS AND FINANCIAL CONDITION"

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "SEC"
            and "8-K" in event.title.upper()
            and self._PATTERN in event.summary.upper()
        )

    def build_summary(self, event: Event) -> str:
        return "החברה דיווחה על תוצאותיה הכספיות."