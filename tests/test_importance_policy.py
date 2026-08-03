from models.event import Event
from product.importance_policy import ImportancePolicy
from models.investor_intelligence_card import ImportanceLevel


def make_event(importance: int) -> Event:
    return Event(
        symbol="TEST",
        source="SEC",
        title="Test",
        summary="Test",
        published_at="2026-08-03T10:00:00+00:00",
        importance=importance,
        sentiment="neutral",
    )


def test_importance_9_is_critical():
    level = ImportancePolicy().classify(make_event(9))

    assert level is ImportanceLevel.CRITICAL


def test_importance_7_is_high():
    level = ImportancePolicy().classify(make_event(7))

    assert level is ImportanceLevel.HIGH


def test_importance_4_is_moderate():
    level = ImportancePolicy().classify(make_event(4))

    assert level is ImportanceLevel.MODERATE