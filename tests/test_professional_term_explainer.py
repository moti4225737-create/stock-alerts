from presentation.professional_term_explainer import (
    ProfessionalTermExplainer,
)


def test_explains_known_professional_terms() -> None:
    explainer = ProfessionalTermExplainer()

    assert explainer.explain("SEC Filing: 10-Q") == (
        "\u05d3\u05d5\u05d7 "
        "\u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 "
        "\u05d7\u05d3\u05e9\n"
        "(SEC Form 10-Q)"
    )
    assert explainer.explain("SEC Filing: 10-K") == (
        "\u05d3\u05d5\u05d7 "
        "\u05e9\u05e0\u05ea\u05d9 "
        "\u05d7\u05d3\u05e9\n"
        "(SEC Form 10-K)"
    )
    assert explainer.explain("SEC Filing: 8-K") == (
        "\u05d3\u05d9\u05d5\u05d5\u05d7 "
        "\u05de\u05d4\u05d5\u05ea\u05d9 "
        "\u05d7\u05d3\u05e9\n"
        "(SEC Form 8-K)"
    )
    assert explainer.explain("PDUFA") == (
        "\u05de\u05d5\u05e2\u05d3 "
        "\u05d4\u05d7\u05dc\u05d8\u05ea FDA\n"
        "(PDUFA)"
    )
    assert explainer.explain("IND") == (
        "\u05d1\u05e7\u05e9\u05d4 "
        "\u05dc\u05d4\u05ea\u05d7\u05dc\u05ea "
        "\u05e0\u05d9\u05e1\u05d5\u05d9 "
        "\u05e7\u05dc\u05d9\u05e0\u05d9\n"
        "(IND)"
    )


def test_returns_unknown_term_unchanged() -> None:
    explainer = ProfessionalTermExplainer()

    assert explainer.explain("Unknown Code") == "Unknown Code"
