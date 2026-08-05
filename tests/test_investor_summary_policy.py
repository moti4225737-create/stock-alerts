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
        "ה-FDA פרסם הודעת החזרה מהשוק "
        "מסוג Class II למוצר של החברה."
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
        "הניסוי הקליני נמצא כעת בסטטוס Recruiting."
    )


def test_builds_annual_sec_filing_summary():
    summary = InvestorSummaryPolicy().build(
        make_event("SEC Filing: 10-K", source="SEC")
    )

    assert summary == (
        "החברה פרסמה את הדוח השנתי שלה ל-SEC."
    )


def test_builds_proxy_statement_summary():
    summary = InvestorSummaryPolicy().build(
        make_event("SEC Filing: DEF 14A", source="SEC")
    )

    assert summary == (
        "החברה פרסמה מסמכים לקראת אסיפת בעלי המניות."
    )


def test_builds_shelf_registration_summary():
    summary = InvestorSummaryPolicy().build(
        make_event("SEC Filing: S-3", source="SEC")
    )

    assert summary == (
        "החברה הגישה ל-SEC תשקיף מדף שעשוי לאפשר גיוס הון עתידי."
    )


def test_builds_summary_from_sec_description():
    summary = InvestorSummaryPolicy().build(
        make_event(
            "SEC Filing: 8-K",
            source="SEC",
            summary="Entry into a Material Definitive Agreement",
        )
    )

    assert summary == (
        "החברה דיווחה על התקשרות בהסכם מהותי חדש."
    )

def test_builds_financial_results_summary_from_sec_description():
    summary = InvestorSummaryPolicy().build(
        make_event(
            "SEC Filing: 8-K",
            source="SEC",
            summary="Results of Operations and Financial Condition",
        )
    )

    assert summary == (
        "החברה דיווחה על תוצאותיה הכספיות."
    )


def test_builds_leadership_change_summary_from_sec_description():
    summary = InvestorSummaryPolicy().build(
        make_event(
            "SEC Filing: 8-K",
            source="SEC",
            summary=(
                "Departure of Directors or Certain Officers; "
                "Election of Directors; Appointment of Certain Officers"
            ),
        )
    )

    assert summary == (
        "החברה דיווחה על שינוי בהנהלה או בדירקטוריון."
    )


class FakeInvestorSummaryRuleSet:
    def __init__(self, summary: str) -> None:
        self._summary = summary
        self.received_events: list[Event] = []

    def build(self, event: Event) -> str:
        self.received_events.append(event)
        return self._summary


def test_delegates_summary_building_to_rule_set():
    event = make_event(
        "SEC Filing: 8-K",
        source="SEC",
        summary="Raw provider summary",
    )
    rule_set = FakeInvestorSummaryRuleSet(
        "Rule-set generated summary"
    )
    policy = InvestorSummaryPolicy(rule_set=rule_set)

    assert policy.build(event) == "Rule-set generated summary"
    assert rule_set.received_events == [event]

def test_default_policy_uses_specific_sec_rule_before_generic_8k_rule():
    event = make_event(
        "SEC Filing: 8-K",
        source="SEC",
        summary="Entry into a Material Definitive Agreement",
    )

    assert InvestorSummaryPolicy().build(event) == (
        "החברה דיווחה על התקשרות בהסכם מהותי חדש."
    )


def test_default_policy_uses_generic_8k_rule_as_fallback():
    event = make_event(
        "SEC Filing: 8-K",
        source="SEC",
        summary="Unrecognized SEC description",
    )

    assert InvestorSummaryPolicy().build(event) == (
        "החברה פרסמה דיווח מיידי על אירוע מהותי ל-SEC."
    )

def test_default_policy_uses_fda_recall_rule():
    event = make_event(
        "FDA Drug Recall — Class II — Liquidia Technologies",
        source="FDA",
        summary=(
            "Example recall reason"
            " | Product: Example drug product"
            " | Recall number: D-1234"
            " | Status: Ongoing"
        ),
    )

    assert InvestorSummaryPolicy().build(event) == (
        "ה-FDA פרסם הודעת החזרה מהשוק "
        "מסוג Class II למוצר של החברה."
    )


def test_default_policy_uses_clinical_trial_status_rule():
    event = make_event(
        "Clinical Trial — Yutrepia Study",
        source="ClinicalTrials.gov",
        summary=(
            "NCT ID: NCT01234567"
            " | Status: RECRUITING"
        ),
    )

    assert InvestorSummaryPolicy().build(event) == (
        "הניסוי הקליני נמצא כעת בסטטוס Recruiting."
    )

def test_interpret_builds_structured_material_agreement_result():
    result = InvestorSummaryPolicy().interpret(
        make_event(
            "SEC Filing: 8-K",
            source="SEC",
            summary="Entry into a Material Definitive Agreement",
        )
    )

    assert result.summary == (
        "החברה דיווחה על התקשרות בהסכם מהותי חדש."
    )
    assert result.explanation.why_it_matters == (
        "הסכם מהותי עשוי לשנות את התחייבויות החברה, "
        "מקורות ההכנסה שלה או הסיכונים העסקיים שלה."
    )
    assert result.explanation.market_context == (
        "יש לבחון את הצדדים להסכם, היקפו, תנאיו "
        "והשפעתו האפשרית על התחזית הפיננסית."
    )

def test_interpret_supports_sec_quarterly_report():
    event = make_event(
        "SEC Filing: 10-Q",
        source="SEC",
        summary="Quarterly report",
    )

    result = InvestorSummaryPolicy().interpret(event)

    assert result.summary == (
        "\u05d4\u05d7\u05d1\u05e8\u05d4 "
        "\u05e4\u05e8\u05e1\u05de\u05d4 "
        "\u05d3\u05d5\u05d7 "
        "\u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 "
        "\u05d7\u05d3\u05e9 "
        "\u05dc-SEC."
    )
    assert result.explanation.why_it_matters
    assert result.explanation.market_context

def test_interpret_supports_sec_annual_report():
    event = make_event(
        "SEC Filing: 10-K",
        source="SEC",
        summary="Annual report",
    )

    result = InvestorSummaryPolicy().interpret(event)

    assert result.summary == (
        "\u05d4\u05d7\u05d1\u05e8\u05d4 "
        "\u05e4\u05e8\u05e1\u05de\u05d4 "
        "\u05d0\u05ea "
        "\u05d4\u05d3\u05d5\u05d7 "
        "\u05d4\u05e9\u05e0\u05ea\u05d9 "
        "\u05e9\u05dc\u05d4 "
        "\u05dc-SEC."
    )
    assert result.explanation.why_it_matters
    assert result.explanation.market_context

def test_interpret_supports_sec_proxy_statement():
    event = make_event(
        "SEC Filing: DEF 14A",
        source="SEC",
        summary="Proxy statement",
    )

    result = InvestorSummaryPolicy().interpret(event)

    assert result.summary == (
        "\u05d4\u05d7\u05d1\u05e8\u05d4 "
        "\u05e4\u05e8\u05e1\u05de\u05d4 "
        "\u05de\u05e1\u05de\u05db\u05d9\u05dd "
        "\u05dc\u05e7\u05e8\u05d0\u05ea "
        "\u05d0\u05e1\u05d9\u05e4\u05ea "
        "\u05d1\u05e2\u05dc\u05d9 "
        "\u05d4\u05de\u05e0\u05d9\u05d5\u05ea."
    )
    assert result.explanation.why_it_matters
    assert result.explanation.market_context

def test_interpret_supports_sec_shelf_registration():
    event = make_event(
        "SEC Filing: S-3",
        source="SEC",
        summary="Shelf registration",
    )

    result = InvestorSummaryPolicy().interpret(event)

    assert result.summary == (
        "\u05d4\u05d7\u05d1\u05e8\u05d4 "
        "\u05d4\u05d2\u05d9\u05e9\u05d4 "
        "\u05dc-SEC "
        "\u05ea\u05e9\u05e7\u05d9\u05e3 "
        "\u05de\u05d3\u05e3 "
        "\u05e9\u05e2\u05e9\u05d5\u05d9 "
        "\u05dc\u05d0\u05e4\u05e9\u05e8 "
        "\u05d2\u05d9\u05d5\u05e1 "
        "\u05d4\u05d5\u05df "
        "\u05e2\u05ea\u05d9\u05d3\u05d9."
    )
    assert result.explanation.why_it_matters
    assert result.explanation.market_context
