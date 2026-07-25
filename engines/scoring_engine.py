from models.event import Event


class ScoringEngine:
    """
    Calculates an importance score for an Event.
    """

    SEC_FORM_SCORES = {
        "8-K": 8,
        "10-K": 7,
        "10-Q": 7,
        "6-K": 8,
        "20-F": 8,
    }

    def score(self, event: Event) -> int:
        """
        Return an importance score between 1 and 10.
        """
        if event.source.upper() == "SEC":
            form = self._extract_sec_form(event)

            if form:
                return self.SEC_FORM_SCORES.get(form, 5)

            return 5

        return 1

    def _extract_sec_form(self, event: Event) -> str | None:
        """
        Extract the SEC form type from the event title.

        Expected title format:
        SEC Filing: 8-K
        """
        prefix = "SEC Filing:"

        if not event.title.startswith(prefix):
            return None

        form = event.title.removeprefix(prefix).strip()

        if not form:
            return None

        return form