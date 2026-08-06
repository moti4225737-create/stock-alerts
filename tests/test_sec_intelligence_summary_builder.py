from product.sec_intelligence_summary_builder import (
    SECIntelligenceSummaryBuilder,
)


def test_builds_compact_hebrew_summary_from_financial_signals() -> None:
    builder = SECIntelligenceSummaryBuilder()

    summary = builder.build(
        {
            "revenue": "increased 18%",
            "cash": "$412 million",
            "net_loss": "$7 million",
        }
    )

    assert summary == (
        "\u05d4\u05d4\u05db\u05e0\u05e1\u05d5\u05ea "
        "\u05e2\u05dc\u05d5 \u05d1-18%. "
        "\u05d9\u05ea\u05e8\u05ea \u05d4\u05de\u05d6\u05d5\u05de\u05e0\u05d9\u05dd "
        "\u05e2\u05de\u05d3\u05d4 \u05e2\u05dc $412 million, "
        "\u05d5\u05d4\u05d4\u05e4\u05e1\u05d3 \u05d4\u05e0\u05e7\u05d9 "
        "\u05e2\u05de\u05d3 \u05e2\u05dc $7 million."
    )


def test_returns_empty_summary_without_signals() -> None:
    builder = SECIntelligenceSummaryBuilder()

    assert builder.build({}) == ""
