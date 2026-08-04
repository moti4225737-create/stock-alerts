from models.event import Event


class InvestorSummaryPolicy:
    def build(self, event: Event) -> str:
        source = event.source.upper()
        title = event.title.upper()

        if source == "SEC" and "8-K" in title:
            return (
                "החברה פרסמה דיווח מיידי "
                "על אירוע מהותי ל-SEC."
            )

        if source == "SEC" and "10-Q" in title:
            return "החברה פרסמה דוח רבעוני חדש ל-SEC."

        return event.summary