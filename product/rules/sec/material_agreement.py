from models.event import Event


class SecMaterialAgreementSummaryRule:
    rule_id = "sec.8k.material_agreement"
    priority = 300

    _PATTERN = "ENTRY INTO A MATERIAL DEFINITIVE AGREEMENT"

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "SEC"
            and "8-K" in event.title.upper()
            and self._PATTERN in event.summary.upper()
        )

    def build_summary(self, event: Event) -> str:
        return (
            "החברה דיווחה על התקשרות "
            "בהסכם מהותי חדש."
        )