from models.event import Event
from models.investor_intelligence_card import EventCategory
from product.event_category_policy import EventCategoryPolicy


def make_event(title: str, source: str = "SEC") -> Event:
    return Event(
        symbol="TEST",
        source=source,
        title=title,
        summary="Test",
        published_at="2026-08-03T10:00:00+00:00",
        importance=8,
        sentiment="neutral",
    )


def test_sec_8k_is_material_filing():
    category = EventCategoryPolicy().classify(
        make_event("SEC Filing: 8-K")
    )

    assert category is EventCategory.MATERIAL_FILING


def test_non_sec_8k_title_is_corporate_disclosure():
    category = EventCategoryPolicy().classify(
        make_event("8-K discussion", source="NEWS")
    )

    assert category is EventCategory.CORPORATE_DISCLOSURE


def test_other_titles_are_corporate_disclosure():
    category = EventCategoryPolicy().classify(
        make_event("Management Update")
    )

    assert category is EventCategory.CORPORATE_DISCLOSURE