from models.event import Event
from product.story_correlator import StoryCorrelator


def event(
    symbol: str,
    title: str,
    summary: str,
    published_at: str,
) -> Event:
    return Event(
        symbol=symbol,
        source="Benchmark",
        title=title,
        summary=summary,
        published_at=published_at,
        importance=8,
        sentiment="neutral",
        url="https://example.com/event",
    )


def test_different_named_acquisition_targets_are_definitive_non_match() -> None:
    cyberhawk = event(
        "ONDS",
        "Ondas completes Cyberhawk acquisition",
        "Ondas completed the purchase of Cyberhawk Holdings.",
        "2026-08-10",
    )

    dzyne = event(
        "ONDS",
        "Ondas completes DZYNE acquisition",
        "Ondas completed the acquisition of DZYNE Technologies.",
        "2026-08-25",
    )

    result = StoryCorrelator().correlate(
        earlier_event=cyberhawk,
        current_event=dzyne,
    )

    assert not result.is_correlated
    assert result.confidence == 1.0


def test_same_asset_different_story_domains_are_definitive_non_match() -> None:
    approval = event(
        "LQDA",
        "FDA approves YUTREPIA",
        (
            "FDA approved YUTREPIA for the treatment "
            "of pulmonary hypertension."
        ),
        "2025-05-23",
    )

    litigation = event(
        "LQDA",
        "YUTREPIA patent litigation update",
        (
            "The company reported developments in "
            "patent litigation involving YUTREPIA."
        ),
        "2026-03-31",
    )

    result = StoryCorrelator().correlate(
        earlier_event=approval,
        current_event=litigation,
    )

    assert not result.is_correlated
    assert result.confidence == 1.0


def test_different_reporting_periods_are_not_one_story() -> None:
    q1 = event(
        "LQDA",
        "Liquidia reports Q1 results",
        (
            "Liquidia reported first-quarter revenue "
            "and operating results."
        ),
        "2026-05-08",
    )

    q2 = event(
        "LQDA",
        "Liquidia reports Q2 results",
        (
            "Liquidia reported second-quarter revenue "
            "and operating results."
        ),
        "2026-08-07",
    )

    result = StoryCorrelator().correlate(
        earlier_event=q1,
        current_event=q2,
    )

    assert not result.is_correlated
    assert result.confidence == 1.0


def test_implicit_reference_routes_to_semantic_fallback() -> None:
    announced = event(
        "ONDS",
        "Strategic acquisition announced",
        (
            "Ondas agreed to purchase the UK-based "
            "drone inspection company Cyberhawk."
        ),
        "2026-06-18",
    )

    closing = event(
        "ONDS",
        "Transaction closing",
        (
            "The previously announced purchase of the "
            "inspection company has now closed."
        ),
        "2026-08-10",
    )

    result = StoryCorrelator().correlate(
        earlier_event=announced,
        current_event=closing,
    )

    assert not result.is_correlated
    assert result.confidence == 0.5
    assert result.reason
