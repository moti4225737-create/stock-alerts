from models.event import Event


class PointsToWatchPolicy:
    def build(self, event: Event) -> tuple[str, ...]:
        if event.source.upper() == "SEC" and "8-K" in event.title.upper():
            return (
                "לבדוק את תוכן הדיווח.",
                "לעקוב אחר תגובת השוק.",
            )

        return ("לעקוב אחר התפתחויות נוספות.",)