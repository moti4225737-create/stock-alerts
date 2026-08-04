from models.event import Event
from product.points_to_watch_policy import PointsToWatchPolicy


def make_event(title: str, source: str) -> Event:
    return Event(
        symbol="LQDA",
        source=source,
        title=title,
        summary="Test",
        published_at="2026-08-03T10:00:00+00:00",
        importance=9,
        sentiment="neutral",
    )


def test_sec_filing_returns_sec_specific_points():
    points = PointsToWatchPolicy().build(
        make_event("SEC Filing: 8-K", source="SEC")
    )

    assert points == (
        "בדוק את הדיווח המקורי.",
        "עקוב אחר תגובת השוק.",
        "חפש חדשות משלימות.",
    )


def test_clinical_trial_returns_trial_specific_points():
    points = PointsToWatchPolicy().build(
        make_event(
            "Clinical Trial Status Update",
            source="ClinicalTrials.gov",
        )
    )

    assert points == (
        "בדוק את דף הניסוי.",
        "בחן את שינוי הסטטוס.",
        "בדוק את לוחות הזמנים.",
    )


def test_fda_event_returns_fda_specific_points():
    points = PointsToWatchPolicy().build(
        make_event("FDA Decision", source="FDA")
    )

    assert points == (
        "בדוק את הודעת ה-FDA.",
        "זהה את המוצר הרלוונטי.",
        "בחן את משמעות ההחלטה.",
    )


def test_other_events_return_generic_monitoring_point():
    points = PointsToWatchPolicy().build(
        make_event("Management Update", source="NEWS")
    )

    assert points == (
        "עקוב אחר התפתחויות מהותיות נוספות.",
    )