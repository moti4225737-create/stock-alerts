from models.event import Event


class SecLeadershipChangeSummaryRule:
    rule_id = "sec.8k.leadership_change"
    priority = 300

    _PATTERNS = (
        "DEPARTURE OF DIRECTORS OR CERTAIN OFFICERS",
        "APPOINTMENT OF CERTAIN OFFICERS",
        "ELECTION OF DIRECTORS",
    )

    def matches(self, event: Event) -> bool:
        raw_summary = event.summary.upper()

        return (
            event.source.upper() == "SEC"
            and "8-K" in event.title.upper()
            and any(
                pattern in raw_summary
                for pattern in self._PATTERNS
            )
        )

    def build_summary(self, event: Event) -> str:
        return (
            "החברה דיווחה על שינוי "
            "בהנהלה או בדירקטוריון."
        )