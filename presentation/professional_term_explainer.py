class ProfessionalTermExplainer:
    _EXPLANATIONS = {
        "8-K": (
            "Form 8-K",
            "דיווח מיידי על אירוע מהותי בחברה",
        ),
        "PDUFA": (
            "PDUFA",
            "המועד שבו ה-FDA צפוי לפרסם החלטה בבקשת אישור התרופה",
        ),
        "IND": (
            "IND",
            "בקשה להתחלת ניסוי קליני",
        ),
    }

    def explain(self, term: str) -> str:
        canonical_code = self._extract_canonical_code(term)
        explanation = self._EXPLANATIONS.get(canonical_code)

        if explanation is None:
            return term

        display_name, description = explanation
        return f"{display_name}\n({description})"

    def _extract_canonical_code(self, term: str) -> str:
        normalized = term.strip().upper()

        if "8-K" in normalized:
            return "8-K"

        if "PDUFA" in normalized:
            return "PDUFA"

        if "IND" in normalized:
            return "IND"

        return term