from unittest.mock import Mock

import main
from models.event import Event


def test_run_live_preview_sends_quote_alert():
    pipeline = Mock()
    pipeline.collect_events.return_value = []

    quote_fetcher = Mock(
        return_value={
            "c": 67.25,
        }
    )
    telegram_sender = Mock()

    main.run_live_preview(
        watchlist=["LQDA"],
        pipeline=pipeline,
        quote_fetcher=quote_fetcher,
        telegram_sender=telegram_sender,
    )

    quote_fetcher.assert_called_once_with("LQDA")
    pipeline.collect_events.assert_called_once_with("LQDA")
    telegram_sender.assert_called_once()

    sent_message = telegram_sender.call_args.args[0]

    assert "LQDA" in sent_message
    assert "Finnhub" in sent_message
    assert "67.25" in sent_message


def test_run_live_preview_sends_provider_events():
    event = Event(
        symbol="LQDA",
        source="ClinicalTrials.gov",
        title="Clinical Trial — Test Study",
        summary="A clinical study was found.",
        published_at="2026-07-26",
        importance=2,
        sentiment="neutral",
        url="https://clinicaltrials.gov/study/NCT00000001",
    )

    pipeline = Mock()
    pipeline.collect_events.return_value = [event]

    quote_fetcher = Mock(
        return_value={
            "c": 67.25,
        }
    )
    telegram_sender = Mock()

    main.run_live_preview(
        watchlist=["LQDA"],
        pipeline=pipeline,
        quote_fetcher=quote_fetcher,
        telegram_sender=telegram_sender,
    )

    assert telegram_sender.call_count == 2

    event_message = telegram_sender.call_args_list[1].args[0]

    assert "LQDA" in event_message
    assert "ClinicalTrials.gov" in event_message
    assert "Clinical Trial — Test Study" in event_message
    assert "A clinical study was found." in event_message
    assert "2026-07-26" in event_message
    assert "https://clinicaltrials.gov/study/NCT00000001" in event_message