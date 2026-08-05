from models.event import Event


class FdaDrugRecallSummaryRule:
    rule_id = "fda.drug_recall"
    priority = 300

    def matches(self, event: Event) -> bool:
        return (
            event.source.upper() == "FDA"
            and "DRUG RECALL" in event.title.upper()
        )

    def build_summary(self, event: Event) -> str:
        title = event.title.upper()

        if "CLASS III" in title:
            classification = "Class III"
        elif "CLASS II" in title:
            classification = "Class II"
        elif "CLASS I" in title:
            classification = "Class I"
        else:
            classification = None

        if classification is None:
            return (
                "ה-FDA פרסם הודעת החזרה מהשוק "
                "למוצר של החברה."
            )

        return (
            "ה-FDA פרסם הודעת החזרה מהשוק "
            f"מסוג {classification} למוצר של החברה."
        )
