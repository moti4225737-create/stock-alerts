class ProfessionalTermExplainer:
    _EXPLANATIONS = {
        "10-Q": (
            "\u05d3\u05d5\u05d7 "
            "\u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 "
            "\u05d7\u05d3\u05e9",
            "SEC Form 10-Q",
        ),
        "10-K": (
            "\u05d3\u05d5\u05d7 "
            "\u05e9\u05e0\u05ea\u05d9 "
            "\u05d7\u05d3\u05e9",
            "SEC Form 10-K",
        ),
        "8-K": (
            "\u05d3\u05d9\u05d5\u05d5\u05d7 "
            "\u05de\u05d4\u05d5\u05ea\u05d9 "
            "\u05d7\u05d3\u05e9",
            "SEC Form 8-K",
        ),
        "PDUFA": (
            "\u05de\u05d5\u05e2\u05d3 "
            "\u05d4\u05d7\u05dc\u05d8\u05ea FDA",
            "PDUFA",
        ),
        "IND": (
            "\u05d1\u05e7\u05e9\u05d4 "
            "\u05dc\u05d4\u05ea\u05d7\u05dc\u05ea "
            "\u05e0\u05d9\u05e1\u05d5\u05d9 "
            "\u05e7\u05dc\u05d9\u05e0\u05d9",
            "IND",
        ),
    }

    def explain(self, term: str) -> str:
        canonical_code = self._extract_canonical_code(term)
        explanation = self._EXPLANATIONS.get(canonical_code)

        if explanation is None:
            return term

        business_title, technical_name = explanation
        return f"{business_title}\n({technical_name})"

    def _extract_canonical_code(self, term: str) -> str:
        normalized = term.strip().upper()

        for code in (
            "10-Q",
            "10-K",
            "8-K",
            "PDUFA",
            "IND",
        ):
            if code in normalized:
                return code

        return normalized
