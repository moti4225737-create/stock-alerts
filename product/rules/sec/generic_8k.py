from models.event import Event


class Sec8KSummaryRule:
    rule_id = "sec.8k.generic"
    priority = 100

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "SEC"
            and "8-K" in event.title.upper()
        )

    def build_summary(self, event: Event) -> str:
        return (
            "החברה פרסמה דיווח מיידי "
            "על אירוע מהותי ל-SEC."
        )