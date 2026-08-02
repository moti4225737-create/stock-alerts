from engines.explanation_engine import ExplanationEngine
from models.event import Event
from models.explanation import Explanation


def test_explanation_engine_supports_sec_8k():
    event = Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 8-K",
        summary="Material event",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )

    engine = ExplanationEngine()
    explanation = engine.explain(event)

    assert explanation == Explanation(
        why_it_matters="Material events can affect investor sentiment and may require close monitoring.",
        market_context="This filing is a significant corporate update that can influence trading and outlook.",
    )


def test_explanation_engine_supports_sec_10q():
    event = Event(
        symbol="AAPL",
        source="SEC",
        title="SEC Filing: 10-Q",
        summary="Quarterly report",
        published_at="2026-08-01T10:00:00+00:00",
        importance=7,
        sentiment="neutral",
    )

    engine = ExplanationEngine()
    explanation = engine.explain(event)

    assert explanation == Explanation(
        why_it_matters="Earnings and operating results can materially influence valuation and investor expectations.",
        market_context="Quarterly reporting often shapes near-term market sentiment and analyst revisions.",
    )


def test_explanation_engine_supports_fda_approval():
    event = Event(
        symbol="NVDA",
        source="FDA",
        title="FDA Approval",
        summary="Drug approved",
        published_at="2026-08-01T10:00:00+00:00",
        importance=9,
        sentiment="positive",
    )

    engine = ExplanationEngine()
    explanation = engine.explain(event)

    assert explanation == Explanation(
        why_it_matters="Approval can unlock commercialization potential and materially change the company outlook.",
        market_context="Regulatory clearance often drives a re-rating of the company’s growth prospects.",
    )


def test_explanation_engine_supports_clinical_trial():
    event = Event(
        symbol="NVDA",
        source="Clinical Trials",
        title="Clinical Trial",
        summary="Trial update",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )

    engine = ExplanationEngine()
    explanation = engine.explain(event)

    assert explanation == Explanation(
        why_it_matters="Clinical progress can influence the probability of future approval and commercialization.",
        market_context="Trial milestones are closely watched because they can alter future revenue and risk assumptions.",
    )


def test_explanation_engine_supports_fomc():
    event = Event(
        symbol="SPY",
        source="Macro",
        title="FOMC",
        summary="Policy decision",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )

    engine = ExplanationEngine()
    explanation = engine.explain(event)

    assert explanation == Explanation(
        why_it_matters="Policy decisions can materially change financing conditions and investor risk appetite.",
        market_context="Central bank decisions often drive broader market direction and sector rotation.",
    )


def test_explanation_engine_supports_cpi():
    event = Event(
        symbol="SPY",
        source="Macro",
        title="CPI",
        summary="Inflation data",
        published_at="2026-08-01T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )

    engine = ExplanationEngine()
    explanation = engine.explain(event)

    assert explanation == Explanation(
        why_it_matters="Inflation data can shape expectations for rates, growth, and corporate earnings.",
        market_context="CPI releases often influence bond yields and broad market sentiment.",
    )


def test_explanation_engine_returns_generic_explanation_for_unknown_events():
    event = Event(
        symbol="AAPL",
        source="News",
        title="Unexpected headline",
        summary="Unexpected summary",
        published_at="2026-08-01T10:00:00+00:00",
        importance=4,
        sentiment="neutral",
    )

    engine = ExplanationEngine()
    explanation = engine.explain(event)

    assert explanation == Explanation(
        why_it_matters="This event may be relevant to market participants and should be monitored.",
        market_context="The broader market impact will depend on how the news is interpreted over time.",
    )
