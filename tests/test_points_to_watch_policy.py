from models.event import Event
from product.points_to_watch_policy import PointsToWatchPolicy


def make_event(title: str, source: str = "SEC") -> Event:
    return Event(
        symbol="LQDA",
        source=source,
        title=title,
        summary="Test",
        published_at="2026-08-03T10:00:00+00:00",
        importance=9,
        sentiment="neutral",
    )


def test_material_sec_filing_returns_expected_points():
    points = PointsToWatchPolicy().build(
        make_event("SEC Filing: 8-K")
    )

    assert points == (
        "לבדוק את תוכן הדיווח.",
        "לעקוב אחר תגובת השוק.",
    )


def test_other_events_return_generic_monitoring_points():
    points = PointsToWatchPolicy().build(
        make_event("Management Update", source="NEWS")
    )

    assert points == (
        "לעקוב אחר התפתחויות נוספות.",
    )