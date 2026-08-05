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

        if source == "SEC" and "10-K" in title:
            return "החברה פרסמה את הדוח השנתי שלה ל-SEC."

        if source == "SEC" and "DEF 14A" in title:
            return (
                "החברה פרסמה מסמכים "
                "לקראת אסיפת בעלי המניות."
            )

        if source == "SEC" and "S-3" in title:
            return (
                "החברה הגישה ל-SEC תשקיף מדף "
                "שעשוי לאפשר גיוס הון עתידי."
            )

        if source == "FDA" and "DRUG RECALL" in title:
            return (
                "ה-FDA פרסם הודעת החזרה מהשוק "
                "למוצר של החברה."
            )

        if (
            source == "CLINICALTRIALS.GOV"
            or "CLINICAL TRIAL" in title
        ):
            return (
                "פורסם עדכון חדש לניסוי הקליני "
                "של החברה."
            )

        return event.summary
