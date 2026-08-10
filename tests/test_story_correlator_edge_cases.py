from models.event import Event
from product.story_correlator import StoryCorrelator


def make_event(
    symbol: str,
    title: str,
    summary: str,
    published_at: str,
) -> Event:
    return Event(
        symbol=symbol,
        source="SEC",
        title=title,
        summary=summary,
        published_at=published_at,
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


def test_correlator_does_not_match_same_term_when_story_is_different() -> None:
    earlier = make_event(
        symbol="ONDS",
        title="Cyberhawk acquisition announced",
        summary=(
            "Ondas agreed to acquire Cyberhawk Holdings."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        symbol="ONDS",
        title="Cyberhawk customer contract",
        summary=(
            "Cyberhawk signed a new inspection services "
            "contract with a utility customer."
        ),
        published_at="2026-08-20",
    )

    result = StoryCorrelator().correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert not result.is_correlated


def test_correlator_matches_same_story_with_different_wording_when_subject_is_explicit() -> None:
    earlier = make_event(
        symbol="ONDS",
        title="Strategic acquisition announced",
        summary=(
            "Ondas agreed to purchase the UK-based "
            "drone inspection business Cyberhawk."
        ),
        published_at="2026-06-18",
    )

    current = make_event(
        symbol="ONDS",
        title="Transaction closing",
        summary=(
            "The previously announced Cyberhawk "
            "purchase has now closed."
        ),
        published_at="2026-08-10",
    )

    result = StoryCorrelator().correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert result.is_correlated
    assert result.confidence == 1.0


def test_correlator_never_matches_different_symbols() -> None:
    earlier = make_event(
        symbol="ONDS",
        title="Acquisition announced",
        summary="The company agreed to acquire Cyberhawk.",
        published_at="2026-06-18",
    )

    current = make_event(
        symbol="LQDA",
        title="Cyberhawk acquisition completed",
        summary="The acquisition of Cyberhawk was completed.",
        published_at="2026-08-10",
    )

    result = StoryCorrelator().correlate(
        earlier_event=earlier,
        current_event=current,
    )

    assert not result.is_correlated
    assert result.confidence == 1.0
