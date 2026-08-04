from models.event import Event
from product.investor_summary_policy import InvestorSummaryPolicy


def make_event(
    title: str,
    source: str,
    summary: str = "Raw provider summary",
) -> Event:
    return Event(
        symbol="LQDA",
        source=source,
        title=title,
        summary=summary,
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )


def test_builds_material_sec_filing_summary():
    summary = InvestorSummaryPolicy().build(
        make_event("SEC Filing: 8-K", source="SEC")
    )

    assert summary == (
        "החברה פרסמה דיווח מיידי על אירוע מהותי ל-SEC."
    )


def test_builds_quarterly_sec_filing_summary():
    summary = InvestorSummaryPolicy().build(
        make_event("SEC Filing: 10-Q", source="SEC")
    )

    assert summary == (
        "החברה פרסמה דוח רבעוני חדש ל-SEC."
    )


def test_preserves_provider_summary_for_unknown_events():
    summary = InvestorSummaryPolicy().build(
        make_event(
            "Management Update",
            source="NEWS",
            summary="Management announced a strategic update.",
        )
    )

    assert summary == "Management announced a strategic update."

def test_builds_fda_recall_summary():
    summary = InvestorSummaryPolicy().build(
        make_event(
            "FDA Drug Recall — Class II — Liquidia Technologies",
            source="FDA",
            summary=(
                "Example recall reason"
                " | Product: Example drug product"
                " | Recall number: D-1234"
                " | Status: Ongoing"
            ),
        )
    )

    assert summary == (
        "ה-FDA פרסם הודעת החזרה מהשוק למוצר של החברה."
    )


def test_builds_clinical_trial_summary():
    summary = InvestorSummaryPolicy().build(
        make_event(
            (
                "Clinical Trial — "
                "A Study of Yutrepia in Participants "
                "With Pulmonary Hypertension"
            ),
            source="ClinicalTrials.gov",
            summary=(
                "This study evaluates the safety and effectiveness "
                "of Yutrepia."
                " | NCT ID: NCT01234567"
                " | Status: RECRUITING"
            ),
        )
    )

    assert summary == (
        "פורסם עדכון חדש לניסוי הקליני של החברה."
    )
