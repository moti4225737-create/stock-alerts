from presentation.professional_term_explainer import (
    ProfessionalTermExplainer,
)


def test_explains_known_professional_terms():
    explainer = ProfessionalTermExplainer()

    assert explainer.explain("SEC Filing: 8-K") == (
        "Form 8-K\n"
        "(דיווח מיידי על אירוע מהותי בחברה)"
    )
    assert explainer.explain("PDUFA") == (
        "PDUFA\n"
        "(המועד שבו ה-FDA צפוי לפרסם החלטה בבקשת אישור התרופה)"
    )
    assert explainer.explain("IND") == (
        "IND\n"
        "(בקשה להתחלת ניסוי קליני)"
    )


def test_returns_unknown_term_unchanged():
    explainer = ProfessionalTermExplainer()

    assert explainer.explain("Unknown Code") == "Unknown Code"