from models.event import Event


class PointsToWatchPolicy:
    def build(self, event: Event) -> tuple[str, ...]:
        source = event.source.upper()
        title = event.title.upper()

        if source == "SEC":
            return (
                "בדוק את הדיווח המקורי.",
                "עקוב אחר תגובת השוק.",
                "חפש חדשות משלימות.",
            )

        if source == "CLINICALTRIALS.GOV" or "CLINICAL TRIAL" in title:
            return (
                "בדוק את דף הניסוי.",
                "בחן את שינוי הסטטוס.",
                "בדוק את לוחות הזמנים.",
            )

        if source == "FDA" or "FDA" in title:
            return (
                "בדוק את הודעת ה-FDA.",
                "זהה את המוצר הרלוונטי.",
                "בחן את משמעות ההחלטה.",
            )

        return (
            "עקוב אחר התפתחויות מהותיות נוספות.",
        )